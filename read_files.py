import os
import spacy
from spacy.matcher import PhraseMatcher
from spacy.lang.en.stop_words import STOP_WORDS
from docx import Document

#spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")


def extract_keywords(text):
    doc = nlp(text)
    keywords = [
    token.lemma_.lower()
    for token in doc
      if token.is_alpha and token.lemma_.lower() not in STOP_WORDS
]
    return set(keywords)


def read_word_files(folder_path, issue):
    relevant_data = []
    issue_keywords = extract_keywords(issue)

    for file in os.listdir(folder_path):
       if file.endswith('.docx'):
         file_path = os.path.join(folder_path, file)
         try:
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            doc_keywords = extract_keywords(text)
            common = issue_keywords.intersection(doc_keywords)
            match_ratio = len(common) / len(issue_keywords)
            if match_ratio >= 0.5:
               relevant_data.append((file, text))
         except Exception as e:
            print('Exception',e)
            continue
    return relevant_data