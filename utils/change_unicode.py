# 유니코드 범위와 상수 정의
JAMO_LEADS = [chr(_) for _ in range(0x1100, 0x1113)]
JAMO_VOWELS = [chr(_) for _ in range(0x1161, 0x1176)]
# 종성 리스트 수정: 복합 종성 포함 처리를 위해 인덱스를 명확히 정의
JAMO_TAILS = ['', 'ᆨ', 'ᆩ', 'ᆪ', 'ᆫ', 'ᆬ', 'ᆭ', 'ᆮ', 'ᆯ', 'ᆰ', 'ᆱ', 'ᆲ', 'ᆳ', 'ᆴ', 'ᆵ', 'ᆶ', 'ᆷ', 'ᆸ', 'ᆹ', 'ᆺ', 'ᆻ', 'ᆼ', 'ᆽ', 'ᆾ', 'ᆿ', 'ᇀ', 'ᇁ', 'ᇂ']  # 복합 종성도 포함

HANGUL_BASE = 0xAC00
NUM_JUNGSEONG = 21
NUM_JONGSEONG = 28

def compose_hangul(choseong, jungseong, jongseong=''):
    choseong_idx = JAMO_LEADS.index(choseong)
    jungseong_idx = JAMO_VOWELS.index(jungseong)
    jongseong_idx = JAMO_TAILS.index(jongseong) if jongseong else 0  # 종성 없는 경우 인덱스 0 처리

    return chr(HANGUL_BASE + choseong_idx * NUM_JUNGSEONG * NUM_JONGSEONG + jungseong_idx * NUM_JONGSEONG + jongseong_idx)

def jamo_to_hangul(text):
    jamo_list = list(text.replace(" ", ""))
    result = []
    i = 0

    while i < len(jamo_list):
        if i+1 < len(jamo_list) and jamo_list[i] in JAMO_LEADS and jamo_list[i+1] in JAMO_VOWELS:
            if i+2 < len(jamo_list) and jamo_list[i+2] in JAMO_TAILS:
                if i+3 >= len(jamo_list) or jamo_list[i+3] in JAMO_LEADS or jamo_list[i+3] in JAMO_VOWELS:
                    # 초성, 중성, 종성 조합
                    result.append(compose_hangul(jamo_list[i], jamo_list[i+1], jamo_list[i+2]))
                    i += 3
                else:
                    # 종성 없는 경우 처리
                    result.append(compose_hangul(jamo_list[i], jamo_list[i+1]))
                    i += 2
            else:
                # 종성이 없는 경우
                result.append(compose_hangul(jamo_list[i], jamo_list[i+1]))
                i += 2
        else:
            # 단독 자모 처리
            result.append(jamo_list[i])
            i += 1
    return ''.join(result)

def read_and_convert(filename):
    # 변환된 내용을 저장할 리스트 초기화
    converted_lines = []
    
    # 파일 읽기
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            # 각 줄을 변환
            converted_line = jamo_to_hangul(line.strip())
            converted_lines.append(converted_line)
    
    return converted_lines

def save_converted_text(converted_lines, output_filename):
    # 변환된 텍스트를 새 파일에 저장
    with open(output_filename, 'w', encoding='utf-8') as file:
        for line in converted_lines:
            file.write(line + '\n')

# 사용 예시
input_filename = 'val.txt'  # 읽을 파일 이름
output_filename = 'val2.txt'  # 저장할 파일 이름

converted_lines = read_and_convert(input_filename)
save_converted_text(converted_lines, output_filename)

print("변환 작업이 완료되었습니다.")
