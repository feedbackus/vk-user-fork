import argparse
import json
import logging
import requests
from neo4j import GraphDatabase


class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def create_user(self, user_data):
        query = """
        MERGE (u:User {id: $id})
        SET u.name = $name, u.screen_name = $screen_name, u.sex = $sex, u.city = $city
        """
        self.run_query(query, user_data)

    def create_group(self, group_data):
        query = """
        MERGE (g:Group {id: $id})
        SET g.name = $name, g.screen_name = $screen_name
        """
        self.run_query(query, group_data)

    def rel_follow(self, user_from, user_to):
        query = """
        MATCH (u1:User {id: $from})
        MATCH (u2:User {id: $to})
        MERGE (u1)-[:FOLLOWS]->(u2)
        """
        self.run_query(query, {'from': user_from, 'to': user_to})

    def rel_sub(self, user, group):
        query = """
        MATCH (u:User {id: $user})
        MATCH  (g:Group {id: $group})
        MERGE (u)-[:SUBSCRIBED]->(g)
        """
        self.run_query(query, {'user': user, 'group': group})
        
    def clear_db(self):
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        self.run_query(query)
            
    def query(self, query_type):
        queries = {
            'users_count': "MATCH (u:User) RETURN COUNT(u) AS count",
            'groups_count': "MATCH (g:Group) RETURN COUNT(g) AS count",
            'top_users': """
                MATCH (u:User)<-[:FOLLOWS]-()
                RETURN u.id, u.name, COUNT(*) AS followers_count
                ORDER BY followers_count DESC LIMIT 5
            """,
            'top_groups': """
                MATCH (g:Group)<-[:SUBSCRIBED]-()
                RETURN g.id, g.name, COUNT(*) AS subscribers_count
                ORDER BY subscribers_count DESC LIMIT 5
            """,
            'mutual_followers': """
                MATCH (u1:User)-[:FOLLOWS]->(u2:User)-[:FOLLOWS]->(u1) 
                RETURN u1.id, u2.id
            """
        }
    
        try:
            result = self.run_query(queries[query_type])
            return result
        except KeyError as ke:
            logger.error(f"такого запроса нет")
            return []      
    
def get_user_info(args, neo4j_handler, user_id, depth=2):
    logger.info(f'fetching info for {user_id}')
    

    user_info_url = f'https://api.vk.com/method/users.get'
    user_info_params = {
        'user_ids': user_id,
        'fields': 'city,sex,screen_name',
        'access_token': args.token,
        'v': '5.199'
    }
    user_response = requests.get(user_info_url, params=user_info_params)
    user_data = user_response.json()    
    if 'error' in user_data:
        error_msg = user_data['error'].get('error_msg', 'Unknown error')
        logger.error(f"Error fetching user info: {error_msg}")
        return
    if len(user_data['response']) == 0:
        logger.error(f"No info: {user_response.text}")
        return

    user = user_data['response'][0]

    user_dict = {
        'id': user['id'],
        'name': user['first_name'] + ' ' + user['last_name'],
        'screen_name': user.get('screen_name', ''),
        'sex': user.get('sex', ''),
        'city': user.get('city', {}).get('title', '') if user.get('city') else ''
    }
    logger.info(f"user: {user_dict}")
    neo4j_handler.create_user(user_dict)

    followers_url = f'https://api.vk.com/method/users.getFollowers'
    followers_params = {
        'user_id': user['id'],
        'access_token': args.token,
        'v': '5.199'
    }

    followers_response = requests.get(followers_url, params=followers_params)
    followers_data = followers_response.json()
    followers = followers_data.get('response', {}).get('items', [])

    subscriptions_url = f'https://api.vk.com/method/users.getSubscriptions'
    subscriptions_params = {
        'user_id': user['id'],
        'extended': 1,
        'access_token': args.token,
        'v': '5.199'
    }

    subscriptions_response = requests.get(subscriptions_url, params=subscriptions_params)
    subscriptions_data = subscriptions_response.json()
    groups = subscriptions_data.get('response', {}).get('items', [])

    for follower in followers:
        logger.info(f"follower: {follower}")
        neo4j_handler.rel_follow(follower, user['id'])
        if depth > 1:
            get_user_info(args, neo4j_handler, follower, depth - 1)

    for group in groups:
        if group['type'] == 'profile':
            continue

        group_data = {
            'id': group['id'],
            'name': group['name'],
            'screen_name': group.get('screen_name', '')
        }
        neo4j_handler.create_group(group_data)
        neo4j_handler.rel_sub(user['id'], group['id'])
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--user_id', type=str, help='ID VK user')
    parser.add_argument('--token', type=str, help='Access token VK')
    parser.add_argument('--query', type=str, help='users_count, groups_count, top_users, top_groups, mutual_followers')
    parser.add_argument('--depth', type=int, help='fetching depth')
    parser.add_argument('--neo4j_uri', type=str, default='neo4j://localhost:7687', help='URI neo4j')
    parser.add_argument('--neo4j_login', type=str, default='neo4j',help='login neo4j')
    parser.add_argument('--neo4j_pass', type=str, default='11111111',help='password neo4j')
    parser.add_argument('--clear', action='store_true', help='clear database')

    args = parser.parse_args()

    logging.basicConfig(level='INFO', format='%(asctime)s [%(levelname)s]: %(message)s')
    logger = logging.getLogger(__name__)

    neo4j_handler = Neo4jHandler(args.neo4j_uri, args.neo4j_login, args.neo4j_pass)

    if args.query:
        result = neo4j_handler.query(args.query)
        
        if args.query in ['users_count', 'groups_count']:
            print(result[0]['count'])
        elif args.query == 'top_users':
            if result:
                for record in result:
                    print(f"{record['u.name']}, followers: {record['followers_count']}")
            else:
                print("not found")
        elif args.query == 'top_groups':
            if result:
                for record in result:
                    print(f"{record['g.name']}, subscribers: {record['subscribers_count']}")
            else:
                print("not found")
        elif args.query == 'mutual_followers':
            if result:
                for record in result:
                    print(f"{record['u1.id']} - {record['u2.id']}")
            else:
                print("not found")
    else:
        if args.clear:
            logger.info("clearing db...")
            neo4j_handler.clear_db()
        get_user_info(args, neo4j_handler, args.user_id, depth=args.depth)

    neo4j_handler.close()