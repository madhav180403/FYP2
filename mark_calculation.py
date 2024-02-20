from pymongo import MongoClient
from transformers import BertTokenizer, BertModel
import torch
from torch.nn.functional import cosine_similarity
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['automatic_grading']
questions_collection = db['questions']
students_collection = db['student']
teachers_collection = db['teacher']
student_responses_collection = db['student_responses']

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def calc_marks(question_id,student_answer):

    document = questions_collection.find_one({"_id": ObjectId(question_id)})

    expected_answer = document['answer'].lower()

    inputs1 = tokenizer(expected_answer, return_tensors="pt", padding=True, truncation=True)
    inputs2 = tokenizer(student_answer, return_tensors="pt", padding=True, truncation=True)

    input_ids1 = inputs1['input_ids']
    attention_mask1 = inputs1['attention_mask']

    input_ids2 = inputs2['input_ids']
    attention_mask2 = inputs2['attention_mask']

    with torch.no_grad():
        outputs1 = model(input_ids1, attention_mask=attention_mask1)
        embeddings1 = torch.mean(outputs1.last_hidden_state, dim=1)

    with torch.no_grad():
        outputs2 = model(input_ids2, attention_mask=attention_mask2)
        embeddings2 = torch.mean(outputs2.last_hidden_state, dim=1)


    similarity = cosine_similarity(embeddings1, embeddings2).item()

    marks = 0

    if(similarity > 0.85):
        marks = 1
    
    elif(similarity > 0.5):
        marks = 0.5

    return marks


