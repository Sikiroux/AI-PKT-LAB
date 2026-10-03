"""
twofish_pure.py — Chiffrement Twofish (clé 128 bits) en pur Python.

Pourquoi : le paquet PyPI 'twofish' n'existe qu'en code source C et exige un
compilateur Visual C++ sous Windows. Le mode EAX utilisé par Packet Tracer
n'a besoin que de l'opération de CHIFFREMENT d'un bloc, implémentée ici
d'après la spécification de Schneier et al. (1998).
Validé contre la bibliothèque C de référence (vecteurs officiels + blocs aléatoires).
"""

_Q0_T = ([8, 1, 7, 13, 6, 15, 3, 2, 0, 11, 5, 9, 14, 12, 10, 4],
         [14, 12, 11, 8, 1, 2, 3, 5, 15, 4, 10, 6, 7, 0, 9, 13],
         [11, 10, 5, 14, 6, 13, 9, 0, 12, 8, 15, 3, 2, 4, 7, 1],
         [13, 7, 15, 4, 1, 2, 6, 14, 9, 11, 3, 0, 8, 5, 12, 10])
_Q1_T = ([2, 8, 11, 13, 15, 7, 6, 14, 3, 1, 9, 4, 0, 10, 12, 5],
         [1, 14, 2, 11, 4, 12, 3, 7, 6, 13, 10, 5, 15, 9, 0, 8],
         [4, 12, 7, 5, 1, 6, 9, 10, 0, 14, 13, 8, 2, 11, 3, 15],
         [11, 9, 5, 1, 12, 3, 13, 14, 6, 4, 7, 15, 2, 0, 8, 10])


def _ror4(x, n):
    return ((x >> n) | (x << (4 - n))) & 0xF


def _make_q(t):
    out = []
    for x in range(256):
        a0, b0 = x >> 4, x & 0xF
        a1 = a0 ^ b0
        b1 = a0 ^ _ror4(b0, 1) ^ ((8 * a0) & 0xF)
        a2, b2 = t[0][a1], t[1][b1]
        a3 = a2 ^ b2
        b3 = a2 ^ _ror4(b2, 1) ^ ((8 * a2) & 0xF)
        a4, b4 = t[2][a3], t[3][b3]
        out.append((b4 << 4) | a4)
    return out


Q0, Q1 = _make_q(_Q0_T), _make_q(_Q1_T)


def _gf_mul(a, b, poly):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= poly
        b >>= 1
    return r


_MDS = ((0x01, 0xEF, 0x5B, 0x5B), (0x5B, 0xEF, 0xEF, 0x01),
        (0xEF, 0x5B, 0x01, 0xEF), (0xEF, 0x01, 0xEF, 0x5B))
_RS = ((0x01, 0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E),
       (0xA4, 0x56, 0x82, 0xF3, 0x1E, 0xC6, 0x68, 0xE5),
       (0x02, 0xA1, 0xFC, 0xC1, 0x47, 0xAE, 0x3D, 0x19),
       (0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E, 0x03))

# Tables précalculées MDS[i][j] * y pour accélérer (le chiffrement est appelé des milliers de fois)
_MDS_T = [[[_gf_mul(_MDS[i][j], y, 0x169) for y in range(256)] for j in range(4)] for i in range(4)]

_M32 = 0xFFFFFFFF


def _rol(x, n):
    return ((x << n) | (x >> (32 - n))) & _M32


def _ror(x, n):
    return ((x >> n) | (x << (32 - n))) & _M32


def _h(x, l):
    """Fonction h pour une clé de 128 bits (k = 2). l = [L0, L1]."""
    y = [(x >> (8 * i)) & 0xFF for i in range(4)]
    l0 = [(l[0] >> (8 * i)) & 0xFF for i in range(4)]
    l1 = [(l[1] >> (8 * i)) & 0xFF for i in range(4)]
    y = [Q1[Q0[Q0[y[0]] ^ l1[0]] ^ l0[0]],
         Q0[Q0[Q1[y[1]] ^ l1[1]] ^ l0[1]],
         Q1[Q1[Q0[y[2]] ^ l1[2]] ^ l0[2]],
         Q0[Q1[Q1[y[3]] ^ l1[3]] ^ l0[3]]]
    z = 0
    for i in range(4):
        z |= (_MDS_T[i][0][y[0]] ^ _MDS_T[i][1][y[1]] ^ _MDS_T[i][2][y[2]] ^ _MDS_T[i][3][y[3]]) << (8 * i)
    return z


class Twofish:
    """Interface compatible avec le paquet 'twofish' : Twofish(key).encrypt(block)."""

    def __init__(self, key: bytes):
        if len(key) != 16:
            raise ValueError('Seules les clés de 128 bits sont gérées')
        m = [int.from_bytes(key[4 * i:4 * i + 4], 'little') for i in range(4)]
        me, mo = [m[0], m[2]], [m[1], m[3]]
        s = []
        for i in range(2):
            chunk = key[8 * i:8 * i + 8]
            word = 0
            for r in range(4):
                v = 0
                for c in range(8):
                    v ^= _gf_mul(_RS[r][c], chunk[c], 0x14D)
                word |= v << (8 * r)
            s.append(word)
        self._s = [s[1], s[0]]
        rho = 0x01010101
        self._k = []
        for i in range(20):
            a = _h((2 * i * rho) & _M32, me)
            b = _rol(_h(((2 * i + 1) * rho) & _M32, mo), 8)
            self._k.append((a + b) & _M32)
            self._k.append(_rol((a + 2 * b) & _M32, 9))
        # g(X) = h(X, S) : précalcul des 4 tables octet -> mot (clé fixe)
        s0, s1 = self._s
        b0 = [(s0 >> (8 * i)) & 0xFF for i in range(4)]
        b1 = [(s1 >> (8 * i)) & 0xFF for i in range(4)]
        self._g = [
            [_MDS_T_col(0, Q1[Q0[Q0[y] ^ b1[0]] ^ b0[0]]) for y in range(256)],
            [_MDS_T_col(1, Q0[Q0[Q1[y] ^ b1[1]] ^ b0[1]]) for y in range(256)],
            [_MDS_T_col(2, Q1[Q1[Q0[y] ^ b1[2]] ^ b0[2]]) for y in range(256)],
            [_MDS_T_col(3, Q0[Q1[Q1[y] ^ b1[3]] ^ b0[3]]) for y in range(256)],
        ]

    def _gfun(self, x):
        g = self._g
        return (g[0][x & 0xFF] ^ g[1][(x >> 8) & 0xFF] ^ g[2][(x >> 16) & 0xFF] ^ g[3][x >> 24])

    def encrypt(self, block: bytes) -> bytes:
        k = self._k
        r = [int.from_bytes(block[4 * i:4 * i + 4], 'little') ^ k[i] for i in range(4)]
        r0, r1, r2, r3 = r
        for rnd in range(16):
            t0 = self._gfun(r0)
            t1 = self._gfun(_rol(r1, 8))
            f0 = (t0 + t1 + k[2 * rnd + 8]) & _M32
            f1 = (t0 + 2 * t1 + k[2 * rnd + 9]) & _M32
            r2 = _ror(r2 ^ f0, 1)
            r3 = _rol(r3, 1) ^ f1
            r0, r1, r2, r3 = r2, r3, r0, r1
        out = (r2 ^ k[4], r3 ^ k[5], r0 ^ k[6], r1 ^ k[7])
        return b''.join(w.to_bytes(4, 'little') for w in out)


def _MDS_T_col(j, y):
    """Colonne j de la multiplication MDS pour un octet y, sous forme de mot 32 bits."""
    return (_MDS_T[0][j][y] | (_MDS_T[1][j][y] << 8) | (_MDS_T[2][j][y] << 16) | (_MDS_T[3][j][y] << 24))
