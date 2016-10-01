'''QPack - (de)serializer

:copyright: 2016, Jeroen van der Heijden (Transceptor Technology)
'''
import sys
import struct

# for being Python2 and Python3 compatible
PY_CONVERT = ord if sys.version_info[0] == 2 else int

SIZE8_T = struct.Struct('<B')
SIZE16_T = struct.Struct('<H')
SIZE32_T = struct.Struct('<I')
SIZE64_T = struct.Struct('<Q')

INT8_T = struct.Struct('<b')
INT16_T = struct.Struct('<h')
INT32_T = struct.Struct('<i')
INT64_T = struct.Struct('<q')

DOUBLE = struct.Struct('<d')

# Fixed integer lengths: b'\x00' - '\x3f'
# Fixed negative integer lengths: b'\x40' - '\x7c'
# Fixed doubles: -1.0 0.0 and 1.0  '\x7d', '\x7e', '\x7f'
QP_DOUBLE_N1 = b'\x7d'
QP_DOUBLE_0 = b'\x7e'
QP_DOUBLE_1 = b'\x7f'

# Fixed str lengths: b'\x80' - '\xe3'  (0 .. 99)

QP_RAW8 = b'\xe4'   # 228
QP_RAW16 = b'\xe5'
QP_RAW32 = b'\xe6'
QP_RAW64 = b'\xe7'

QP_INT8 = b'\xe8'   # 232
QP_INT16 = b'\xe9'
QP_INT32 = b'\xea'
QP_INT64 = b'\xeb'

QP_DOUBLE = b'\xec' # 236 this one is 8 bytes, reserve for 4 bytes

START_ARR = 237
QP_ARRAY0 = b'\xed' # 237
QP_ARRAY1 = b'\xee'
QP_ARRAY2 = b'\xef'
QP_ARRAY3 = b'\xf0'
QP_ARRAY4 = b'\xf1'
QP_ARRAY5 = b'\xf2'

START_MAP = 243
QP_MAP0 = b'\xf3'   # 243
QP_MAP1 = b'\xf4'
QP_MAP2 = b'\xf5'
QP_MAP3 = b'\xf6'
QP_MAP4 = b'\xf7'
QP_MAP5 = b'\xf8'

QP_BOOL_TRUE = b'\xf9' # 249
QP_BOOL_FALSE = b'\xfa'
QP_NULL = b'\xfb'

QP_OPEN_ARRAY, N_OPEN_ARRAY = b'\xfc', 252
QP_OPEN_MAP, N_OPEN_MAP = b'\xfd', 253
QP_CLOSE_ARRAY, N_CLOSE_ARRAY = b'\xfe', 254
QP_CLOSE_MAP, N_CLOSE_MAP = b'\xff', 255

_RAW_MAP = {
    ord(QP_RAW8): SIZE8_T,
    ord(QP_RAW16): SIZE16_T,
    ord(QP_RAW32): SIZE32_T,
    ord(QP_RAW64): SIZE64_T}

_NUMBER_MAP = {
    ord(QP_INT8): INT8_T,
    ord(QP_INT16): INT16_T,
    ord(QP_INT32): INT32_T,
    ord(QP_INT64): INT64_T,
    ord(QP_DOUBLE): DOUBLE}

_SIMPLE_MAP = {
    ord(QP_BOOL_TRUE): True,
    ord(QP_BOOL_FALSE): False,
    ord(QP_NULL): None}


def _pack(obj, container):
    if obj is True:
        container.append(QP_BOOL_TRUE)

    elif obj is False:
        container.append(QP_BOOL_FALSE)

    elif obj is None:
        container.append(QP_NULL)

    elif isinstance(obj, int):
        if 64 > obj >= 0:
            container.append(struct.pack("B", obj))
            return
        if 0 > obj >= -61:
            container.append(struct.pack("B", 63 - obj))
            return

        bit_len = obj.bit_length()
        if bit_len < 8:
            container.append(QP_INT8)
            container.append(INT8_T.pack(obj))
        elif bit_len < 16:
            container.append(QP_INT16)
            container.append(INT16_T.pack(obj))
        elif bit_len < 32:
            container.append(QP_INT32)
            container.append(INT32_T.pack(obj))
        elif bit_len < 64:
            container.append(QP_INT64)
            container.append(INT64_T.pack(obj))
        else:
            raise OverflowError(
                'QuickPack allows up to 64bit signed integers, '
                'got bit length: {}'.format(bit_len))

    elif isinstance(obj, float):
        if obj == 0.0:
            container.append(QP_DOUBLE_0)
        elif obj == 1.0:
            container.append(QP_DOUBLE_1)
        elif obj == -1.0:
            container.append(QP_DOUBLE_N1)
        else:
            container.append(QP_DOUBLE)
            container.append(DOUBLE.pack(obj))

    elif isinstance(obj, str):
        b = obj.encode('utf-8')
        l = len(b)
        if l < 100:
            container.append(struct.pack("B", 128 + l))
        elif l < 256:
            container.append(QP_RAW8)
            container.append(SIZE8_T.pack(l))
        elif l < 65536:
            container.append(QP_RAW16)
            container.append(SIZE16_T.pack(l))
        elif l < 4294967296:
            container.append(QP_RAW32)
            container.append(SIZE32_T.pack(l))
        elif l < 18446744073709551616:
            container.append(QP_RAW64)
            container.append(SIZE64_T.pack(l))
        else:
            raise ValueError(
                'raw string length too large to fit in QuickPack: {}'
                .format(l))
        container.append(b)

    elif isinstance(obj, bytes):
        l = len(obj)
        if l < 100:
            container.append(struct.pack("B", 128 + l))
        elif l < 256:
            container.append(QP_RAW8)
            container.append(SIZE8_T.pack(l))
        elif l < 65536:
            container.append(QP_RAW16)
            container.append(SIZE16_T.pack(l))
        elif l < 4294967296:
            container.append(QP_RAW32)
            container.append(SIZE32_T.pack(l))
        elif l < 18446744073709551616:
            container.append(QP_RAW64)
            container.append(SIZE64_T.pack(l))
        else:
            raise ValueError(
                'raw string length too large to fit in QuickPack: {}'
                .format(l))
        container.append(obj)

    elif isinstance(obj, (list, tuple)):
        l = len(obj)
        if l < 6:
            container.append(SIZE8_T.pack(START_ARR + l))
            for value in obj:
                _pack(value, container)
        else:
            container.append(QP_OPEN_ARRAY)
            for value in obj:
                _pack(value, container)
            container.append(QP_CLOSE_ARRAY)

    elif isinstance(obj, dict):
        l = len(obj)
        if l < 6:
            container.append(SIZE8_T.pack(START_MAP + l))
            for key, value in obj.items():
                _pack(key, container)
                _pack(value, container)
        else:
            container.append(QP_OPEN_MAP)
            for key, value in obj.items():
                _pack(key, container)
                _pack(value, container)
            container.append(QP_CLOSE_MAP)


def _unpack(qp, pos, end, decode=None):
    tp = PY_CONVERT(qp[pos])
    pos += 1
    if tp < 64:
        return pos, tp

    if tp < 125:
        return pos, 63 - tp

    if tp < 0x80:
        return pos, float(tp - 126)

    if tp < 0xe4:
        end_pos = pos + (tp - 128)
        return end_pos, qp[pos:end_pos] if decode is None \
            else qp[pos:end_pos].decode(decode)

    if tp < 0xe8:
        qp_type = _RAW_MAP[tp]
        end_pos = pos + qp_type.size + qp_type.unpack_from(qp, pos)[0]
        pos += qp_type.size
        return end_pos, qp[pos:end_pos] if decode is None \
            else qp[pos:end_pos].decode(decode)

    if tp < 0xed: # double included
        qp_type = _NUMBER_MAP[tp]
        return pos + qp_type.size, qp_type.unpack_from(qp, pos)[0]

    if tp < 0xf3:
        qp_array = []
        for _ in range(tp - 0xed):
            pos, value = _unpack(qp, pos, end, decode)
            qp_array.append(value)
        return pos, qp_array

    if tp < 0xf9:
        qp_map = {}
        for _ in range(tp - 0xf3):
            pos, key = _unpack(qp, pos, end, decode)
            pos, value = _unpack(qp, pos, end, decode)
            qp_map[key] = value
        return pos, qp_map

    if tp < 0xfc:
        return pos, _SIMPLE_MAP[tp]

    if tp == N_OPEN_ARRAY:
        qp_array = []
        while pos < end and qp[pos] != N_CLOSE_ARRAY:
            pos, value = _unpack(qp, pos, end, decode)
            qp_array.append(value)
        return pos + 1, qp_array

    if tp == N_OPEN_MAP:
        qp_map = {}
        while pos < end and qp[pos] != N_CLOSE_MAP:
            pos, key = _unpack(qp, pos, end, decode)
            pos, value = _unpack(qp, pos, end, decode)
            qp_map[key] = value
        return pos + 1, qp_map

    raise ValueError('Error in quickpack at position {}'.format(pos))


def packb(obj):
    container = []
    _pack(obj, container)
    return b''.join(container)


def unpackb(qp, decode=None):
    return _unpack(qp, 0, len(qp), decode=decode)[1]


if __name__ == '__main__':
    pass


