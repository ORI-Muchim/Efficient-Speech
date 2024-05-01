# Code based on 

import re
import os
import ast
import json
from jamo import h2j, hangul_to_jamo, j2h, jamo_to_hcj

from .ko_dictionary import english_dictionary, etc_dictionary, num_to_kor, unit_to_kor1, unit_to_kor2, upper_to_kor

PAD = '_'
EOS = '~'
PUNC = '!\'(),-.:;?{}[]'
SPACE = ' '
_SILENCES = ['sp', 'spn', 'sil']

JAMO_LEADS = "".join([chr(_) for _ in range(0x1100, 0x1113)])
JAMO_VOWELS = "".join([chr(_) for _ in range(0x1161, 0x1176)])
JAMO_TAILS = "".join([chr(_) for _ in range(0x11A8, 0x11C3)])

VALID_CHARS = JAMO_LEADS + JAMO_VOWELS + JAMO_TAILS + PUNC + SPACE
ALL_SYMBOLS = list(PAD + EOS + VALID_CHARS) + _SILENCES

symbol_to_id = {c: i for i, c in enumerate(ALL_SYMBOLS)}
id_to_char = {i: c for i, c in enumerate(ALL_SYMBOLS)}

quote_checker = """([`"'＂“‘])(.+?)([`"'＂”’])"""


def is_lead(char):
    return char in JAMO_LEADS


def is_vowel(char):
    return char in JAMO_VOWELS


def is_tail(char):
    return char in JAMO_TAILS


def get_mode(char):
    if is_lead(char):
        return 0
    elif is_vowel(char):
        return 1
    elif is_tail(char):
        return 2
    else:
        return -1


def _get_text_from_candidates(candidates):
    if len(candidates) == 0:
        return ""
    elif len(candidates) == 1:
        return jamo_to_hcj(candidates[0])
    else:
        return j2h(**dict(zip(["lead", "vowel", "tail"], candidates)))


def jamo_to_korean(text):
    text = h2j(text)

    idx = 0
    new_text = ""
    candidates = []

    while True:
        if idx >= len(text):
            new_text += _get_text_from_candidates(candidates)
            break

        char = text[idx]
        mode = get_mode(char)

        if mode == 0:
            new_text += _get_text_from_candidates(candidates)
            candidates = [char]
        elif mode == -1:
            new_text += _get_text_from_candidates(candidates)
            new_text += char
            candidates = []
        else:
            candidates.append(char)

        idx += 1
    return new_text


def compare_sentence_with_jamo(text1, text2):
    return h2j(text1) != h2j(text2)


def tokenize(text, as_id=False):
    # Normalize the input text
    text = normalize(text)
    tokens = list(hangul_to_jamo(text))  # Example: '존경하는' --> ['ᄌ', 'ᅩ', 'ᆫ', 'ᄀ', 'ᅧ', 'ᆼ', 'ᄒ', 'ᅡ', 'ᄂ', 'ᅳ', 'ᆫ', '~']

    tokens = [token for token in tokens if token.strip()]

    if as_id:
        return [symbol_to_id.get(token, symbol_to_id[PAD]) for token in tokens]
    else:
        return tokens


def tokenizer_fn(iterator):
    return (token for x in iterator for token in tokenize(x, as_id=False))


def normalize(text):
    text = text.strip()

    text = re.sub(r'\s{2,}', '', text)

    text = re.sub("\(\d+일\)", "", text)
    text = re.sub("\([⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]+\)", "", text)

    text = normalize_with_dictionary(text, etc_dictionary)
    text = normalize_english(text)
    text = re.sub("[a-zA-Z]+", normalize_upper, text)

    text = number_to_hangul(text)

    text = normalize_quote(text)
    text = normalize_number(text)

    return text


def normalize_with_dictionary(text, dic):
    if any(key in text for key in dic.keys()):
        pattern = re.compile("|".join(re.escape(key) for key in dic.keys()))
        return pattern.sub(lambda x: dic[x.group()], text)
    else:
        return text


def normalize_english(text):
    def fn(m):
        word = m.group()
        if word in english_dictionary:
            return english_dictionary.get(word)
        else:
            return word

    text = re.sub("([A-Za-z]+)", fn, text)
    return text


def normalize_upper(text):
    text = text.group(0)

    if all([char.isupper() for char in text]):
        return "".join(upper_to_kor[char] for char in text)
    else:
        return text


# From CjangCjengh/vits/blob/main/text/korean.py #
_korean_classifiers = '군데 권 개 그루 닢 대 두 마리 모 모금 뭇 발 발짝 방 번 벌 보루 살 수 술 시 쌈 움큼 정 짝 채 척 첩 축 켤레 톨 통'

def hangul_number(num, sino=True):
    '''Reference https://github.com/Kyubyong/g2pK'''
    num = re.sub(',', '', num)

    if num == '0':
        return '영'
    if not sino and num == '20':
        return '스무'

    digits = '123456789'
    names = '일이삼사오육칠팔구'
    digit2name = {d: n for d, n in zip(digits, names)}

    modifiers = '한 두 세 네 다섯 여섯 일곱 여덟 아홉'
    decimals = '열 스물 서른 마흔 쉰 예순 일흔 여든 아흔'
    digit2mod = {d: mod for d, mod in zip(digits, modifiers.split())}
    digit2dec = {d: dec for d, dec in zip(digits, decimals.split())}

    spelledout = []
    for i, digit in enumerate(num):
        i = len(num) - i - 1
        if sino:
            if i == 0:
                name = digit2name.get(digit, '')
            elif i == 1:
                name = digit2name.get(digit, '') + '십'
                name = name.replace('일십', '십')
        else:
            if i == 0:
                name = digit2mod.get(digit, '')
            elif i == 1:
                name = digit2dec.get(digit, '')
        if digit == '0':
            if i % 4 == 0:
                last_three = spelledout[-min(3, len(spelledout)):]
                if ''.join(last_three) == '':
                    spelledout.append('')
                    continue
            else:
                spelledout.append('')
                continue
        if i == 2:
            name = digit2name.get(digit, '') + '백'
            name = name.replace('일백', '백')
        elif i == 3:
            name = digit2name.get(digit, '') + '천'
            name = name.replace('일천', '천')
        elif i == 4:
            name = digit2name.get(digit, '') + '만'
            name = name.replace('일만', '만')
        elif i == 5:
            name = digit2name.get(digit, '') + '십'
            name = name.replace('일십', '십')
        elif i == 6:
            name = digit2name.get(digit, '') + '백'
            name = name.replace('일백', '백')
        elif i == 7:
            name = digit2name.get(digit, '') + '천'
            name = name.replace('일천', '천')
        elif i == 8:
            name = digit2name.get(digit, '') + '억'
        elif i == 9:
            name = digit2name.get(digit, '') + '십'
        elif i == 10:
            name = digit2name.get(digit, '') + '백'
        elif i == 11:
            name = digit2name.get(digit, '') + '천'
        elif i == 12:
            name = digit2name.get(digit, '') + '조'
        elif i == 13:
            name = digit2name.get(digit, '') + '십'
        elif i == 14:
            name = digit2name.get(digit, '') + '백'
        elif i == 15:
            name = digit2name.get(digit, '') + '천'
        spelledout.append(name)
    return ''.join(elem for elem in spelledout)


def number_to_hangul(text):
    '''Reference https://github.com/Kyubyong/g2pK'''
    tokens = set(re.findall(r'(\d[\d,]*)([\uac00-\ud71f]+)', text))
    for token in tokens:
        num, classifier = token
        if classifier[:2] in _korean_classifiers or classifier[0] in _korean_classifiers:
            spelledout = hangul_number(num, sino=False)
        else:
            spelledout = hangul_number(num, sino=True)
        text = text.replace(f'{num}{classifier}', f'{spelledout}{classifier}')
    # digit by digit for remaining digits
    digits = '0123456789'
    names = '영일이삼사오육칠팔구'
    for d, n in zip(digits, names):
        text = text.replace(d, n)
    return text


def normalize_quote(text):
    def fn(found_text):
        from nltk import sent_tokenize  # NLTK doesn't along with multiprocessing

        found_text = found_text.group()
        unquoted_text = found_text[1:-1]

        sentences = sent_tokenize(unquoted_text)
        return " ".join(["'{}'".format(sent) for sent in sentences])

    return re.sub(quote_checker, fn, text)


number_checker = "([+-]?\d[\d,]*)[\.]?\d*"
count_checker = "(시|명|가지|살|마리|포기|송이|수|톨|통|점|개|벌|척|채|다발|그루|자루|줄|켤레|그릇|잔|마디|상자|사람|곡|병|판)"


def normalize_number(text):
    text = normalize_with_dictionary(text, unit_to_kor1)
    text = normalize_with_dictionary(text, unit_to_kor2)
    text = re.sub(
        number_checker + count_checker, lambda x: number_to_korean(x, True), text
    )
    text = re.sub(number_checker, lambda x: number_to_korean(x, False), text)
    return text


num_to_kor1 = [""] + list("일이삼사오육칠팔구")
num_to_kor2 = [""] + list("만억조경해")
num_to_kor3 = [""] + list("십백천")

# count_to_kor1 = [""] + ["하나","둘","셋","넷","다섯","여섯","일곱","여덟","아홉"]
count_to_kor1 = [""] + ["한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"]

count_tenth_dict = {
    "십": "열",
    "두십": "스물",
    "세십": "서른",
    "네십": "마흔",
    "다섯십": "쉰",
    "여섯십": "예순",
    "일곱십": "일흔",
    "여덟십": "여든",
    "아홉십": "아흔",
}


def number_to_korean(num_str, is_count=False):
    if is_count:
        num_str, unit_str = num_str.group(1), num_str.group(2)
    else:
        num_str, unit_str = num_str.group(), ""

    num_str = num_str.replace(",", "")
    num = ast.literal_eval(num_str)

    if num == 0:
        return "영"

    check_float = num_str.split(".")
    if len(check_float) == 2:
        digit_str, float_str = check_float
    elif len(check_float) >= 3:
        raise Exception(" [!] Wrong number format")
    else:
        digit_str, float_str = check_float[0], None

    if is_count and float_str is not None:
        raise Exception(" [!] `is_count` and float number does not fit each other")

    digit = int(digit_str)

    if digit_str.startswith("-"):
        digit, digit_str = abs(digit), str(abs(digit))

    kor = ""
    size = len(str(digit))
    tmp = []

    for i, v in enumerate(digit_str, start=1):
        v = int(v)

        if v != 0:
            if is_count:
                tmp += count_to_kor1[v]
            else:
                tmp += num_to_kor1[v]

            tmp += num_to_kor3[(size - i) % 4]

        if (size - i) % 4 == 0 and len(tmp) != 0:
            kor += "".join(tmp)
            tmp = []
            kor += num_to_kor2[int((size - i) / 4)]

    if is_count:
        if kor.startswith("한") and len(kor) > 1:
            kor = kor[1:]

        if any(word in kor for word in count_tenth_dict):
            kor = re.sub(
                "|".join(count_tenth_dict.keys()),
                lambda x: count_tenth_dict[x.group()],
                kor,
            )

    if not is_count and kor.startswith("일") and len(kor) > 1:
        kor = kor[1:]

    if float_str is not None:
        kor += "쩜 "
        kor += re.sub("\d", lambda x: num_to_kor[x.group()], float_str)

    if num_str.startswith("+"):
        kor = "플러스 " + kor
    elif num_str.startswith("-"):
        kor = "마이너스 " + kor

    return kor + unit_str

if __name__ == "__main__":
    def test_normalize(text):
        print(text)
        print(normalize(text))
        print("="*30)

    test_normalize("JTBC는 JTBCs를 DY는 A가 Absolute")
    test_normalize("오늘(13일) 101마리 강아지가")
    test_normalize('"저돌"(猪突) 입니다.')
    test_normalize('비대위원장이 지난 1월 이런 말을 했습니다. “난 그냥 산돼지처럼 돌파하는 스타일이다”')
    test_normalize("지금은 -12.35%였고 종류는 5가지와 19가지, 그리고 55가지였다")
    test_normalize("JTBC는 TH와 K 양이 2017년 9월 12일 오후 12시에 24살이 된다")