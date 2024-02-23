from pymongo import MongoClient
from sentence_transformers import SentenceTransformer, util
import torch
from bson import ObjectId
import os

client = MongoClient('mongodb://localhost:27017/')
db = client['automatic_grading']
questions_collection = db['questions']
students_collection = db['student']
teachers_collection = db['teacher']
student_responses_collection = db['student_responses']

model_names = [
    'paraphrase-MiniLM-L6-v2',
    'stsb-distilroberta-base-v2',
    'paraphrase-xlm-r-multilingual-v1'
]

save_dir = 'models'
models = [SentenceTransformer(os.path.join(save_dir, model_name)) for model_name in model_names]

def calc_marks(question_id, student_answer):
    
    document = questions_collection.find_one({"_id": ObjectId(question_id)})
    expected_answer = document['answer'].lower()
    
    similarities = 0
    i=0
    with torch.no_grad():
        for model in models:
            embeddings1 = model.encode([expected_answer], convert_to_tensor=True)
            embeddings2 = model.encode([student_answer], convert_to_tensor=True)

            similarity = util.pytorch_cos_sim(embeddings1, embeddings2).item()
            similarities += similarity

            print("Model", i+1," similarity score: ", similarity)

            i+=1

    similarity = similarities / len(models)

    print("Average similarity: ",similarity)
    marks = 0
    if similarity >= 0.9:
        marks = 2
    elif similarity >= 0.77:
        marks = 1
    elif similarity >= 0.65:
        marks = 0.5

    return marks,max(0,similarity),expected_answer
