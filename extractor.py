import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, simpledialog
import os
import re
from collections import Counter

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

        
def reposition_page_markers(text: str) -> str:
    # 치환할 약어와 플레이스홀더
    # 차후에 개발 목표에 따라 추가 및 변동 가능.
    ignored_abbrs = {
        "U.S.A.": "PLACEHOLDER_USA",
        "e.g.": "PLACEHOLDER_EG",
        "i.e.": "PLACEHOLDER_IE"
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
    
    # 3단계: 플레이스홀더 원래 약어로 복원
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

def extractor(doc, name, detect_words):
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
    """
    GUI 입력 대화상자를 통해 학자 키워드를 입력받습니다.
    여러 키워드는 쉼표로 구분하여 입력합니다.
    입력이 없으면 빈 리스트를 반환합니다.
    """
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

def extract_text_from_pdf(file_path, detect_words = '', master=None):
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
