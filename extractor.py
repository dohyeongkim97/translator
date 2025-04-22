import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import re
from collections import Counter

# def extractor(doc, name):
#     new_txt = ''
#     tags = ''
#     detect_words = ['International Security ', 'Foreign Affairs', 'Henry E. Hale is', 'Michael McFaul is', \
#                     'Victor D. Cha is', 'Eric Heginbotham is ']
#     for text_num in range(len(doc)):
#         appearance = 0
#         new_txt += f'[page {text_num+1}]'
#         tags += f'[page {text_num+1}]'
#         temp_txt = ''
#         temp_tags = ''
#         for phrase in doc[text_num].get_text().split('\n'):
#             if (text_num == 0) and ('1. ' in phrase):
#                 appearance = 1
#                 temp_tags += phrase + ' \n'
#             # 그 외 조건들
#             elif (phrase == name) or any(sub in phrase for sub in detect_words):
#                 appearance = 1
#                 temp_tags += phrase + ' \n'
#             elif appearance == 1:
#                 temp_tags += phrase + ' \n'
#             else:
#                 temp_txt += phrase + ' \n'

#         # 텍스트 후처리
#         temp_txt = re.sub(r'\.(\d+)', '.', temp_txt)
#         temp_txt = temp_txt.replace('- \n', '').replace('.\n', '마침표') \
#                            .replace('. \n', '마침표').replace('\n\n', '|space|').replace('\n', '') 
#         temp_txt = temp_txt.replace('마침표', '.\n').replace('|space|', '\n\n')

#         temp_tags = temp_tags.replace('- \n', '').replace('.\n', '마침표') \
#                              .replace('. \n', '마침표').replace('\n\n', '|space|').replace('\n', '')
#         temp_tags = temp_tags.replace('마침표', '.\n').replace('|space|', '\n\n')

#         new_txt += temp_txt + '\n\n'
#         tags += temp_tags + '\n\n'

#     return new_txt, tags
# def reposition_page_markers(text: str) -> str:

#     parts = re.split(r"(\n\n\[page \d+\])", text)
#     if len(parts) <= 1:
#         return text

#     new_parts = [parts[0]]
#     for i in range(1, len(parts), 2):
#         marker = parts[i]           # 예: "\n\n[page 3]"
#         content = parts[i+1] if (i+1) < len(parts) else ""
#         content = content.lstrip()   # 앞쪽 여백 제거

#         prev_text = new_parts[-1]
#         dot_index = prev_text.rfind(".")
#         if dot_index != -1:
#             prev_text = prev_text[:dot_index+1] + marker + " " + prev_text[dot_index+1:]
#             new_parts[-1] = prev_text
#         else:
#             new_parts[-1] = new_parts[-1].rstrip() + marker
#         new_parts.append(content)
#     return "".join(new_parts)


# def reposition_page_markers(text: str) -> str:
#     ignored_abbr = ["U.S.A.", "e.g.", "i.e."]
    
#     def find_valid_period(s: str) -> int:
#         """
#         s 문자열에서 약어에 포함되지 않은 가장 마지막 '.'의 인덱스를 반환합니다.
#         약어에 포함된 점은 무시합니다.
#         """
#         pos = len(s)
#         while True:
#             pos = s.rfind('.', 0, pos)
#             if pos == -1:
#                 return -1
#             # 현재 pos가 포함된 약어가 있는지 체크
#             is_ignored = False
#             for abbr in ignored_abbr:
#                 start = pos - len(abbr) + 1  # 약어 전체 길이를 고려
#                 if start >= 0 and s[start: pos+1] == abbr:
#                     is_ignored = True
#                     break
#             if is_ignored:
#                 pos -= 1  # 약어에 속하는 점이면, 그 앞쪽부터 다시 검색
#                 continue
#             return pos

#     parts = re.split(r"(\n\n\[page \d+\])", text)
#     if len(parts) <= 1:
#         return text

#     new_parts = [parts[0]]
#     for i in range(1, len(parts), 2):
#         marker = parts[i]  # 예: "\n\n[page 3]"
#         content = parts[i+1] if (i+1) < len(parts) else ""
#         content = content.lstrip()   # 앞쪽 공백 제거

#         prev_text = new_parts[-1]
#         dot_index = find_valid_period(prev_text)
#         if dot_index != -1:
#             # 마지막 유효한 '.' 바로 뒤에 페이지 마커를 추가
#             prev_text = prev_text[:dot_index+1] + marker + " " + prev_text[dot_index+1:]
#             new_parts[-1] = prev_text
#         else:
#             new_parts[-1] = new_parts[-1].rstrip() + marker
#         new_parts.append(content)
#     return "".join(new_parts)

def detect_names_from_first_page(text: str) -> list:
    pattern = re.compile(
        r'\b'                                 # 단어 경계
        r'([A-Z][a-zA-Z\.]+(?: [A-Z][a-zA-Z\.]+){1,2})'  
        r'\s+(?:is|are)\b'                    # space + is|are
    )
    names = pattern.findall(text)

    result = []
    seen = set()
    for name in names:
        m = re.search(r'\b' + re.escape(name) + r'\s+(is|are)\b', text)
        if m:
            entry = f"{name} {m.group(1)}"
            if entry not in seen:
                seen.add(entry)
                result.append(entry)

    # 아무것도 없으면 빈 리스트, 있으면 첫 번째만
    return result[:1]

def shifter(new_txt):
    
    text_lists = new_txt.split('\n\n')
    
    for i in range(1, len(text_lists)):
    
        ignored_abbrs = {
            "U.S.A.": "PLACEHOLDER_USA",
            "e.g.": "PLACEHOLDER_EG",
            "i.e.": "PLACEHOLDER_IE",
            "...": "IDKWHYTHISISHERETHOUGH", 
            ". . .": "ANDTHISTOOWHYISTHISHERE?",
            "II.": "세계대전기호",
            "U.S.": "PLACEHOLDER_US",
        }
    
        for abbr, placeholder in ignored_abbrs.items():
            text_lists[i] = text_lists[i].replace(abbr, placeholder)
        
        if text_lists[i-1][-1] != '.':
            pattern = re.compile(r'\[page \d+\]')
            m = pattern.search(text_lists[i])
            prefix = text_lists[i][:m.start()]  
            marker = m.group() 
            suffix = text_lists[i][m.end():] 
    
            text_lists[i] = re.sub(pattern, '', text_lists[i])
    
            dot_idx = text_lists[i].find('.')
    
            text_lists[i-1] += ' ' + text_lists[i][:dot_idx+1]
            text_lists[i] = f'[page {i+1}]' + text_lists[i][dot_idx+1:]
    
            # for abbr, placeholder in ignored_abbrs.items():
            # # placeholder 가 '' 면 스킵
            #     if placeholder == '':
            #         continue

    target_txt = '\n\n'.join(text_lists)
    
    for abbr, placeholder in ignored_abbrs.items():
        target_txt = target_txt.replace(placeholder, abbr)

    return target_txt

    
def reposition_page_markers(text: str) -> str:
    # 치환할 약어와 플레이스홀더
    # 차후에 개발 목표에 따라 추가 및 변동 가능.
    ignored_abbrs = {
        "U.S.A.": "PLACEHOLDER_USA",
        "e.g.": "PLACEHOLDER_EG",
        "i.e.": "PLACEHOLDER_IE",
        "...": "IDKWHYTHISISHERETHOUGH", 
        ". . .": "ANDTHISTOOWHYISTHISHERE?",
        "II.": "세계대전기호",
        "U.S.": "PLACEHOLDER_US",
    }
    
    # 약어 치환
    for abbr, placeholder in ignored_abbrs.items():
        text = text.replace(abbr, placeholder)
    
    # 페이지 구분자를 기준 분할
    parts = re.split(r"(\n\n\[page \d+\])", text)
 
    if len(parts) <= 1:
        for abbr, placeholder in ignored_abbrs.items():
            text = text.replace(placeholder, abbr)
        return text

    new_parts = [parts[0]]
    for i in range(1, len(parts), 2):
        marker = parts[i]  
        content = parts[i+1] if (i+1) < len(parts) else ""
        content = content.lstrip() 

        prev_text = new_parts[-1]
        # 마침표 뒤에 공백과 개행문자가 이어지는 패턴 탐색
        matches = list(re.finditer(r'\.\s*\n', prev_text))
        if matches:
            last_match = matches[-1]
            insertion_index = last_match.end()  # 패턴이 끝나는 위치
            prev_text = prev_text[:insertion_index] + marker + " " + prev_text[insertion_index:]
            new_parts[-1] = prev_text
        else:
            # 패턴이 없으면 기존 방식대로 마커를 텍스트 끝에 추가
            new_parts[-1] = new_parts[-1].rstrip() + marker
        new_parts.append(content)
    
    result = "".join(new_parts)

    for abbr, placeholder in ignored_abbrs.items():
        result = result.replace(placeholder, abbr)
    
    return result

def is_detected_phrase(phrase: str, detect_words: list) -> bool:
    for sub in detect_words:
        if (sub in phrase) and (len(phrase) <= len(sub) + 5):
            return True
    return False

def extract_additional_keywords(text: str, start: int = 1, end: int = 4) -> list:
    full_text = ''
    for i in range(len(text)):
        full_text += '\n'+text[i].get_text()
    
    data = Counter(full_text.split('\n')).most_common()[start:end]    
    return [item[0] for item in data]

def extractor(doc, name, detect_words = None):
    if detect_words == None:
        detect_words = []
    default_detect_words = ['International Security ', 'Foreign Affairs', 'Henry E. Hale is', 
                            'Michael McFaul is', 'Victor D. Cha is', 'Eric Heginbotham is ']
    default_detect_words += extract_additional_keywords(doc)

    first_page_text = doc[0].get_text()
    auto_entries = detect_names_from_first_page(first_page_text)
    auto_names = [entry.rsplit(' ',1)[0] for entry in auto_entries]

    combined = default_detect_words + auto_names
    if detect_words:
        combined += detect_words
    detect_words = list(dict.fromkeys(combined))

    detect_words = [re.sub(r'[^\w\s]', '', w).strip() for w in detect_words]

    print(detect_words)

    new_txt = ''
    tags    = ''
    for text_num in range(len(doc)):
        appearance = 0
        new_txt += f'[page {text_num+1}]'
        tags += f'[page {text_num+1}]'
        temp_txt = ''
        temp_tags = ''
        for phrase in doc[text_num].get_text().split('\n'):
            phrase_detect = re.sub(r'[^\w\s]', '', phrase)
            if (text_num == 0) and (('1. ' in phrase) or (any(phrase_detect.startswith(w.strip()) for w in detect_words))):
                appearance = 1
                temp_tags += phrase + ' \n'
            # 학자 관련 조건 또는 파일 이름과 일치하는 경우
            # elif ((text_num % 2 == 0) and (name in phrase_detect) and (len(name)+5>len(phrase))) or any(sub in phrase for sub in detect_words):
            elif ((text_num % 2 == 0) and (name in phrase_detect) and (len(name)+5 > len(phrase))) \
     or is_detected_phrase(phrase, detect_words):
                appearance = 1
                temp_tags += phrase + ' \n'
            elif appearance == 1:
                temp_tags += phrase + ' \n'
            else:
                temp_txt += phrase + ' \n'

        temp_txt = re.sub(r'\.(\d+)', '.', temp_txt)
        temp_txt = temp_txt.replace('- \n', '').replace('.\n', '마침표') \
                           .replace('. \n', '마침표').replace('\n\n', '|space|').replace('\n', '')
        temp_txt = temp_txt.replace('마침표', '.\n').replace('|space|', '\n\n')
        temp_tags = temp_tags.replace('- \n', '').replace('.\n', '마침표') \
                             .replace('. \n', '마침표').replace('\n\n', '|space|').replace('\n', '')
        temp_tags = temp_tags.replace('마침표', '.\n').replace('|space|', '\n\n')
        
        new_txt += temp_txt + '\n\n'
        tags += temp_tags + '\n\n'
    
    new_txt = reposition_page_markers(new_txt)

    new_txts = new_txt.split('\n\n')

    for i in range(len(new_txts)):
        if new_txts[i].startswith('\n'):
            new_txts[i] = new_txts[i][1:]

    new_txt = '\n\n'.join(new_txts)
    
    return new_txt, tags

def select_pdf_file(master = None):
    """
    GUI 파일 대화상자를 띄워 PDF 파일을 선택한 후 파일 경로를 반환.
    """
    if master is None:
        root = tk.Tk()
        root.withdraw()
    else:
        root = master
    file_path = filedialog.askopenfilename(
        title="PDF 파일 선택",
        filetypes=[("PDF Files", "*.pdf")],
        parent=root
    )
    return file_path

def get_scholar_keywords(master = None):
    if master is None:
        root = tk.Tk()
        root.withdraw()
    else:
        root = master
    scholar_input = simpledialog.askstring(
        "학자 키워드 입력",
        "PDF 첫 페이지의 학자 검출을 위해\n원하는 학자 키워드를 쉼표(,)로 구분하여 입력하세요.\n(입력하지 않으면 건너뜁니다.)",
        parent=root
    )
    if scholar_input:
        detect_words = [word.strip() for word in scholar_input.split(',') if word.strip()]
    else:
        detect_words = []
    return detect_words


def splitter(new_txt):
    print("▶ splitter() 호출됨")

    if '\n' not in new_txt.split('\n\n')[0]:
        print('problem_found')
        location = 7
        temp_str = ''
        while True:
            if new_txt.split('\n\n')[1][location] == '.':
                temp_text = new_txt[:len(new_txt.split('\n\n')[0])] + new_txt[(len(new_txt.split('\n\n')[0]) + location):]
                break
            else:
                location += 1
                temp_str += new_txt.split('\n\n')[1][location]
        
        if (new_txt.split('\n\n')[0][-1] != ' ') and (temp_str[0] != ' '):
            temp_str = ' '+temp_str
        new_txt_temp = new_txt[:len(new_txt.split('\n\n')[0])] + temp_str + '\n\n' \
             + '[page 2]' + new_txt[len(new_txt.split('\n\n')[0])+len(temp_str)+9:]
    else:
        print('no_problem')
        return new_txt
    return new_txt_temp

def extract_text_from_pdf(file_path, detect_words = None, master=None):
    """
    PDF 파일을 열고, 파일 이름(확장자 제외)을 기준으로 extractor를 실행하여
    텍스트와 태그 데이터를 반환.
    """
    if not file_path:
        print("❌ 파일이 선택되지 않았습니다.")
        return None, None, None

    filename_wo_ext = os.path.splitext(os.path.basename(file_path))[0]
    doc = fitz.open(file_path)
    new_txt, tags = extractor(doc, filename_wo_ext, detect_words)
    new_txt = splitter(new_txt)
    new_txt = shifter(new_txt)
    doc.close()
    return new_txt, tags, filename_wo_ext

if __name__ == "__main__":
    file_path = select_pdf_file()

    detect_words = get_scholar_keywords()
    if detect_words:
        print("입력된 학자 키워드:", detect_words)
    else:
        print("학자 키워드가 입력되지 않았습니다. 해당 검출 기능을 건너뜁니다.")

    new_txt, tags, fname = extract_text_from_pdf(file_path, detect_words)
    if new_txt is not None:
        with open(f"{fname}_text.txt", "w", encoding="utf-8") as f:
            f.write(new_txt)
        with open(f"{fname}_tags.txt", "w", encoding="utf-8") as f:
            f.write(tags)
        print("✅ 저장 완료:", fname + "_text.txt", fname + "_tags.txt")