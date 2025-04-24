from dotenv import load_dotenv
load_dotenv()
import gradio as gr
import os
import faiss
import time
import requests
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage


# Set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
github_repo_owner = os.getenv("GITHUB_REPO_OWNER")
github_repo_name = os.getenv("GITHUB_REPO_NAME")
github_token = os.getenv("GITHUB_PAT_TOKEN")

# Company Information
COMPANY_INFO = {
    "name": "Well Architected Foundation",
    "phone": "+1-999-888-666",
    "email": "support@wellarchitected.com",
    "description": "Cloud Architecture and Consulting Services"
}

def load_vectorstore(faiss_index_path):
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key
    )
    vectorstore = FAISS.load_local(
        faiss_index_path,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore

def cite_source(page_content, metadata):
    source_file = metadata.get("source_file", "unknown_file")
    page = metadata.get("page", None)
    if page:
        return f"Source: {source_file}, page {page}"
    else:
        return f"Source: {source_file}"

def check_similarity(question, vectorstore, threshold=0.6):
    """Check if there are any relevant matches in the vectorstore."""
    try:
        docs = vectorstore.similarity_search_with_score(question, k=1)
        if not docs:
            print("No documents found in vectorstore")
            return False
        
        distance = docs[0][1]
        similarity = 1.0 - min(distance, 1.0)
        
        print(f"Similarity score: {similarity}, Threshold: {threshold}")
        return similarity >= threshold
    except Exception as e:
        print(f"Error in similarity check: {str(e)}")
        return False
def create_github_issue(repo_owner, repo_name, token, title, body):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "title": title,
        "body": body
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return f"{response.json()['html_url']}"
    else:
        return f"Error:{response.status_code}, {response.text}"
def generate_answer(question, conversation_history):
    vectorstore = load_vectorstore("faiss_index")
    
    has_relevant_matches = check_similarity(question, vectorstore)
    print(f"Has relevant matches: {has_relevant_matches}")
    
    if not has_relevant_matches:
        return "I apologize, but I couldn't find enough relevant information in the knowledge base to answer your question.", conversation_history
    
    llm = ChatOpenAI(
        model_name="gpt-4",
        openai_api_key=openai_api_key,
        temperature=0
    )
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
        output_key="answer"
    )

    # Add company context to the question
    context_question = f"""Company Context: {COMPANY_INFO['name']} - {COMPANY_INFO['description']}
Contact: {COMPANY_INFO['phone']}, {COMPANY_INFO['email']}

User Question: {question}"""

    result = qa_chain({"question": context_question, "chat_history": conversation_history})
    answer_text = result["answer"]
    updated_history = memory.load_memory_variables({})["chat_history"]
    return answer_text, updated_history

def create_ticket(ticket_description, user_info):
    if not user_info["name"] or not user_info["email"]:
        return "Please fill in your name and email in the sidebar"
    
    title = f"Question from {user_info['name']}"
    body = f"Email: {user_info['email']}\n\nDescription:\n{ticket_description}"
    issue_url = create_github_issue(
        repo_owner=github_repo_owner,
        repo_name=github_repo_name,
        token=github_token,
        title=title,
        body=body
    )
    return f"Ticket created! Link: {issue_url}"

def chat_interface(question, history, user_info):
    if not user_info["name"] or not user_info["email"]:
        return "Please fill in your name and email in the sidebar before starting the chat", history
    
    if not question.strip():
        return "", history
    
    conversation_history = []
    for user_msg, bot_msg in history:
        if user_msg:
            conversation_history.append(HumanMessage(content=user_msg))
        if bot_msg:
            conversation_history.append(AIMessage(content=bot_msg))
    
    answer, updated_history = generate_answer(question, conversation_history)
    
    if "couldn't find enough relevant information" in answer:
        ticket_title = f"Question from {user_info['name']}: {question[:50]}..."
        ticket_body = f"""
Email: {user_info['email']}
Question: {question}

{answer}
"""
        issue_url = create_github_issue(
            repo_owner=github_repo_owner,
            repo_name=github_repo_name,
            token=github_token,
            title=ticket_title,
            body=ticket_body
        )
        answer = f"{answer}\n\nAutomatically created GitHub ticket: {issue_url}"
    
    new_history = history + [(question, answer)]
    return "", new_history

with gr.Blocks(title="Cloud Architect Support Chatbot", theme=gr.themes.Monochrome()) as demo:
    gr.Markdown(f"""
    # Cloud Architect Support Chatbot
    Welcome to the {COMPANY_INFO['name']} support system!
    Phone: {COMPANY_INFO['phone']}, Email: {COMPANY_INFO['email']}
    """)
    
    user_info = gr.State({
        "name": "",
        "email": ""
    })
    
    with gr.Row(equal_height=True):
        with gr.Column(scale=4, min_width=600):
            with gr.Tab("Chat"):
                chatbot = gr.Chatbot(
                    height=500,
                    show_copy_button=True,
                    bubble_full_width=False
                )
                
                # Add status notification
                status_notification = gr.Markdown("""
                ⚠️ **Please complete your profile first**
                To start chatting, please fill in your name and email in the sidebar.
                """, visible=True)
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Enter your question:", 
                        placeholder="Please fill in your profile information first to enable chat...",
                        interactive=False,
                        scale=9
                    )
                    submit_btn = gr.Button("Send", scale=1)
                
                def update_status(name, email):
                    if name and email:
                        return gr.update(visible=False), gr.update(
                            interactive=True,
                            placeholder="Type your question here..."
                        )
                    return gr.update(visible=True), gr.update(
                        interactive=False,
                        placeholder="Please fill in your profile information first to enable chat..."
                    )
                
                msg.submit(chat_interface, [msg, chatbot, user_info], [msg, chatbot])
                submit_btn.click(chat_interface, [msg, chatbot, user_info], [msg, chatbot])
            
            with gr.Tab("Create Ticket"):
                gr.Info("""
                ℹ️ **Profile Information Required**
                Please ensure your name and email are filled in the sidebar before creating a ticket.
                """)
                ticket_description = gr.Textbox(
                    label="Describe your issue or request in detail:", 
                    lines=5,
                    max_lines=10
                )
                submit_btn = gr.Button("Create Ticket")
                output = gr.Textbox(label="Result")
                
                submit_btn.click(
                    create_ticket,
                    inputs=[ticket_description, user_info],
                    outputs=output
                )
        
        # with gr.Column(scale=1, min_width=300):
        with gr.Sidebar():
            with gr.Group():
                gr.Markdown("""## User Information""")
                gr.Info("""
                ⚠️ **Required Fields**
                Please fill in both fields to enable chat and ticket creation.
                """)
                name_input = gr.Textbox(
                    label="Your name:", 
                    placeholder="Enter your name (required)",
                    info="This field is required"
                )
                email_input = gr.Textbox(
                    label="Your email:", 
                    placeholder="Enter your email (required)",
                    info="This field is required"
                )
                
                def update_user_info(name, email):
                    new_info = {
                        "name": name,
                        "email": email
                    }
                    status_update = update_status(name, email)
                    return new_info, status_update[0], status_update[1]
                
                name_input.change(
                    update_user_info,
                    inputs=[name_input, email_input],
                    outputs=[user_info, status_notification, msg]
                )
                email_input.change(
                    update_user_info,
                    inputs=[name_input, email_input],
                    outputs=[user_info, status_notification, msg]
                )


if __name__ == "__main__":
    demo.launch()