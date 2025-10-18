# Quiz: {{ quiz.input_file.stem }}

*Generated from: {{ quiz.input_file.name }}*

{% for question in quiz.questions %}
## Question {{ loop.index }}

**Difficulty:** {{ question.difficulty.title() }}

{{ question.question }}

{% if question.__class__.__name__ == 'MCQQuestion' %}
**Options:**

{% for option in question.shuffled_options %}
{{ loop.index }}. {{ option }}
{% endfor %}
{% else %}
**Answer:** {{ question.answer }}
{% endif %}

**Justification:** {{ question.justification_span }}

---
{% endfor %}
