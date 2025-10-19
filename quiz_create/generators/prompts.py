
# Later, I would like to make the prompt a bit more customizable. Like perhaps specifying the number of each type of question.
#

DEFAULT_PROMPT = """You are generating quiz questions strictly from SOURCE.
Return a JSON list of objects with fields:
 - kind (mcq|cloze|tf|short)
 - question
 - answer
 - distractors(3 for mcq else [])
 - difficulty (easy|medium|hard)
 - justification_span (<=200 chars from SOURCE).
SOURCE:
<<<
{source}
>>>
Write {n} questions.
Return only the Json data. 
"""


