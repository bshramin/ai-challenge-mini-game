import logging

from Config import MAX_MESSAGE_LENGTH

logger = logging.getLogger(__name__)


class MessageType:  # also major_priority
    OUR_QUEEN_MOVING_TO = "1"
    SEEN_SWAMPS = "2"
    SCORPION_IN_POSITION = "3"
    SCORPION_GOT_ATTACKED = "4"
    SCORPION_DIED_IN_POSITION = "5"
    ENEMY_QUEEN_FOUND = "6"


class EasyMessage:
    '''
    message: (type,pos),priority
    priority = min_proirity + major_priority
    '''

    major_priority_map = {
        MessageType.OUR_QUEEN_MOVING_TO: 500,
        MessageType.SEEN_SWAMPS: 10,
        MessageType.SCORPION_IN_POSITION: 200,
        MessageType.SCORPION_GOT_ATTACKED: 100,
        MessageType.SCORPION_DIED_IN_POSITION: 200,
        MessageType.ENEMY_QUEEN_FOUND: 1000,
    }

    @staticmethod
    def pack_messages(message_objects):  # type,(x,y),min_priority
        message_pack = []
        for mtype, mpos, mpriority in message_objects:
            mval = f"{mtype},{mpos[0]},{mpos[1]}"
            priority = EasyMessage.major_priority_map[mtype] + mpriority
            message_pack.append((mval, priority))

        sorted_pack = sorted(message_pack, key=lambda k: k[1], reverse=True)
        message_pack_str = sorted_pack[0][0]
        message_sum_val = sorted_pack[0][1]
        for message in sorted_pack[1:]:
            if len(message_pack_str + message[0]) < MAX_MESSAGE_LENGTH:
                message_pack_str += "|" + message[0]
                message_sum_val += message[1]

        logging.info(f"all messages: {sorted_pack}")
        return message_pack_str, message_sum_val

    @staticmethod
    def unpack_message(messages_str):
        message_objects = dict()
        for message_str in messages_str.split('|'):
            if len(message_str.split(',')) == 3:
                mtype, mpos_x, mpos_y = message_str.split(',')
                if mtype not in message_objects:
                    message_objects[mtype] = []
                message_objects[mtype].append((int(mpos_x), int(mpos_y)))
        return message_objects
