def get_conversations():
    agent1_conversations = [
        ["What is the derivative of x^2?", "Can you explain integration?"],
        ["What is the integral of 1/x?", "Explain limits in calculus."],
        ["How do you solve differential equations?", "What is Laplace transform?"]
    ]

    agent2_conversations = [
        ["Define a pronoun.", "What is an adjective?"],
        ["Explain the past continuous tense.", "What is a conjunction?"],
        ["How to write a persuasive essay?", "Tips for creative writing?"]
    ]

    agent3_conversations = [
        ["What is Newton's first law?", "Explain gravity."],
        ["What is the theory of relativity?", "Describe quantum mechanics."],
        ["Explain photosynthesis.", "What is DNA?"]
    ]

    agent4_conversations = [
        ["Who was Julius Caesar?", "Explain the Renaissance."],
        ["Causes of the French Revolution?", "What was the Industrial Revolution?"],
        ["Impact of World War II?", "What is the Cold War?"]
    ]

    agent5_conversations = [
        ["How to declare a variable in Python?", "What is a function?"],
        ["Explain object-oriented programming.", "What is inheritance in OOP?"],
        ["How to use Git?", "Explain RESTful APIs."]
    ]

    return [
        agent1_conversations,
        agent2_conversations,
        agent3_conversations,
        agent4_conversations,
        agent5_conversations]