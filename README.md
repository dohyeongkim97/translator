# translator

현재는 정치외교학 번역 기준(foreign affairs, international security같은 학술지 위주로 세팅)

env 통해서 chatgpt api 가져올 수 잇움.

토큰 수 계산 정확하지 안음.

논문에서 본문만 추출해서 번역한 다음 txt로 반환함


Translating papers in International Political Deplomacy fields, which is published by International Security or Foreign Affaires.

Chatgpt API can be loaded by env file. 

I tried to calculate tokens and assume the price for translation, but it might not be precise.

Extract the text which is not annotation, and return it as TXT file.

Extract TXT -> Return TXT file -> use returned txt file for translating -> also return translated file.

