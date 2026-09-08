
from app.retrieval.vector_store import query
from app.embedding.embedder import embed_question
from app.generation.llm_client import answer


if __name__ == "__main__":
   """
────────────────────────────────────────
Question: "What is Atlassian's general liability
cap?"
Expected hit: atlassian §14.2
Known answer: (the cap clause)
────────────────────────────────────────
Question: "Which law governs the agreement and
where are disputes heard?"
Expected hit: atlassian §20.4
Known answer: governing law / jurisdiction
────────────────────────────────────────
Question: "Can I get a refund for a cancelled
foodpanda order?"
Expected hit: foodpanda §6.9 (Refunds)
Known answer: only if vendor hasn't accepted
────────────────────────────────────────
Question: "How do I delete my foodpanda account?"
Expected hit: foodpanda §2.3
Known answer: email a request
────────────────────────────────────────
Question: "How can either party terminate the
GitLab agreement?"
Expected hit: gitlab §4.3
Known answer: termination conditions
   """
   question = "Can I get a refund for a cancelled foodpanda order?"
   question_vec = embed_question(question)

   query_result = query(question_vec, 3)
   print("Question = ", question)
   # print("Question vector = ", question_vec)

   # id = query_result["ids"][0]
   # distance = query_result["distances"][0]
   # metadata = query_result["metadatas"][0]
   # document = query_result["documents"][0]

   # print("Query result = ",id, "\n",distance ," \n", metadata, "\n", document, "\n")
   print("============================")

   answer_outcome = answer(question, query_result["documents"])
   print("Ai answer_outcome= ", answer_outcome)



