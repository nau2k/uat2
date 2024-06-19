

from confluent_kafka import Consumer
import requests


conf = {
    'bootstrap.servers': '27.74.253.50:19092',
    'security.protocol': 'SASL_PLAINTEXT',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': 'vinaclient2022009',
    'sasl.password': '6jIZzxCJiJnoM5',
    'group.id': '0307633556',
}
consumer = Consumer(conf)

print (consumer)

print (consumer.list_topics().topics)


running = True

def submit_tvan(message):
    requests.post('https://tvan.latido.vn/tvan/on-message', data={'message': message})

def basic_consume_loop(consumer):
    msg_index = 0
    try:
        topics = consumer.list_topics().topics.get('0307633556_out')
        print ('topics', topics)
        consumer.subscribe(['0307633556_out'])

        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue

            if msg.error():
                print('error:', msg.error())
                submit_tvan(msg.error())
            else:
                msg_index += 1
                print ('Message', msg_index, ':', msg.value(), type(msg.value()))
                submit_tvan(msg.value())
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()

def shutdown():
    running = False

basic_consume_loop(consumer)


# from num2words import num2words
# print (num2words(654040, lang='vi'))