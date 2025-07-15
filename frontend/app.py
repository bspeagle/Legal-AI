"""
Legal AI Virtual Courtroom - Streamlit Frontend
Main application file for user interaction with the virtual courtroom
"""
import streamlit as st
import requests
import json
import os
from datetime import datetime
import pandas as pd
import time

# API Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="Legal AI Virtual Courtroom",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session State Management
if "current_case" not in st.session_state:
    st.session_state.current_case = None
if "current_simulation" not in st.session_state:
    st.session_state.current_simulation = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "participants" not in st.session_state:
    st.session_state.participants = {}
if "documents" not in st.session_state:
    st.session_state.documents = []

# API Helper Functions
def api_request(endpoint, method="GET", data=None, files=None):
    """Make an API request and handle errors"""
    # Ensure API requests go to /api/endpoint
    url = f"{API_URL}/api/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            st.error(f"Unsupported method: {method}")
            return None
            
        if response.status_code >= 400:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
        return response.json()
    except Exception as e:
        st.error(f"API Request Failed: {str(e)}")
        return None

def get_cases():
    """Get list of cases from API"""
    return api_request("cases")

def get_case(case_id):
    """Get case details from API"""
    return api_request(f"cases/{case_id}")

def get_simulations(case_id):
    """Get list of simulations for a case"""
    return api_request(f"simulations?case_id={case_id}")

def create_simulation(case_id, title, conversation_type):
    """Create a new simulation for a case"""
    data = {
        "case_id": case_id,
        "title": title,
        "conversation_type": conversation_type,
        "json_data": {}
    }
    return api_request("simulations", method="POST", data=data)

def get_simulation_messages(simulation_id):
    """Get messages for a simulation"""
    return api_request(f"simulations/{simulation_id}/messages")

def run_simulation_scenario(simulation_id, scenario, speaking_order):
    """Run a simulation scenario"""
    data = {
        "scenario": scenario,
        "speaking_order": speaking_order,
        "context": {}
    }
    return api_request(f"simulations/{simulation_id}/scenario", method="POST", data=data)

def send_message(simulation_id, participant_id, content):
    """Send a message in a simulation"""
    data = {
        "participant_id": participant_id,
        "content": content,
        "json_data": {}
    }
    return api_request(f"simulations/{simulation_id}/messages", method="POST", data=data)

def upload_document(case_id, title, document_type, file):
    """Upload a document for a case"""
    data = {
        "case_id": str(case_id),
        "title": title,
        "document_type": document_type
    }
    files = {
        "file": file
    }
    return api_request(f"documents/upload", method="POST", data=data, files=files)

def analyze_document(document_id, analysis_type="standard"):
    """Analyze a document using AI"""
    data = {
        "document_id": document_id,
        "analysis_type": analysis_type
    }
    return api_request(f"documents/analyze", method="POST", data=data)

def predict_outcome(simulation_id, case_id, scenario_description, factors):
    """Predict case outcome based on simulation data"""
    data = {
        "case_id": case_id,
        "scenario_description": scenario_description,
        "factors": factors
    }
    return api_request(f"simulations/{simulation_id}/predict-outcome", method="POST", data=data)

# UI Components
def render_header():
    """Render the application header"""
    col1, col2 = st.columns([1, 3])
    with col1:
        # Use local logo image instead of external URL
        import os
        logo_path = os.path.join(os.path.dirname(__file__), "static/images/logo.png")
        st.image(logo_path, width=120)
    with col2:
        st.title("Legal AI Virtual Courtroom")
        st.markdown("*An AI-powered legal simulation platform*")

def render_sidebar():
    """Render the sidebar with navigation and options"""
    with st.sidebar:
        st.header("Navigation")
        
        # Case Management
        st.subheader("Case Management")
        if st.button("Create New Case"):
            st.session_state.page = "create_case"
        
        cases = get_cases()
        if cases:
            case_options = {case["title"]: case["id"] for case in cases}
            case_selection = st.selectbox(
                "Select Case",
                options=list(case_options.keys()),
                index=0
            )
            if case_selection:
                selected_case_id = case_options[case_selection]
                if st.button("View Case"):
                    st.session_state.current_case = get_case(selected_case_id)
                    st.session_state.page = "view_case"
        
        # Simulation Control
        if st.session_state.current_simulation:
            st.subheader("Simulation Control")
            if st.button("End Current Simulation"):
                # Update simulation status to completed
                api_request(
                    f"simulations/{st.session_state.current_simulation['id']}",
                    method="PUT",
                    data={"status": "completed"}
                )
                st.session_state.current_simulation = None
                st.rerun()
        
        # Document Management
        st.subheader("Document Management")
        if st.button("Upload Document"):
            st.session_state.page = "upload_document"
        if st.button("View Documents"):
            st.session_state.page = "view_documents"
        
        # Outcome Prediction
        st.subheader("Analysis")
        if st.button("Predict Outcome"):
            st.session_state.page = "predict_outcome"

def create_case_page():
    """Render the create case page"""
    st.header("Create New Case")
    
    with st.form("create_case_form"):
        title = st.text_input("Case Title")
        case_type = st.selectbox(
            "Case Type",
            options=["family", "criminal", "civil", "administrative"]
        )
        description = st.text_area("Case Description")
        
        # Client Information
        st.subheader("Client Information")
        client_name = st.text_input("Client Name")
        client_background = st.text_area("Client Background")
        
        # Opposing Party Information
        st.subheader("Opposing Party Information")
        opposing_name = st.text_input("Opposing Party Name")
        relationship = st.text_input("Relationship to Client")
        opposing_background = st.text_area("Opposing Party Background")
        
        submitted = st.form_submit_button("Create Case")
        
        if submitted and title and case_type:
            # Create case
            case_data = {
                "title": title,
                "case_type": case_type,
                "description": description,
                "json_data": {
                    "client_name": client_name,
                    "client_background": {
                        "background": client_background
                    },
                    "opposing_name": opposing_name,
                    "relationship": relationship,
                    "opposing_background": {
                        "background": opposing_background
                    }
                }
            }
            
            new_case = api_request("cases", method="POST", data=case_data)
            
            if new_case:
                # Create family court simulation
                family_court_data = {
                    "case_title": title,
                    "case_description": description,
                    "client_name": client_name,
                    "opposing_name": opposing_name,
                    "relationship": relationship,
                    "client_background": {
                        "background": client_background
                    },
                    "opposing_background": {
                        "background": opposing_background
                    }
                }
                
                simulation = api_request("agents/family-court", method="POST", data=family_court_data)
                
                if simulation:
                    st.success(f"Case '{title}' created successfully with a family court simulation!")
                    st.session_state.current_case = get_case(new_case["id"])
                    st.session_state.page = "view_case"
                    st.rerun()
                else:
                    st.error("Failed to create family court simulation")
            else:
                st.error("Failed to create case")

def view_case_page():
    """Render the view case page"""
    case = st.session_state.current_case
    if not case:
        st.error("No case selected")
        return
        
    st.header(f"Case: {case['title']}")
    
    # Case Details
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Case Details")
        st.write(f"**Type:** {case['case_type']}")
        st.write(f"**Status:** {case['status']}")
        st.write(f"**Created:** {case['created_at']}")
        
    with col2:
        st.subheader("Description")
        st.write(case['description'] if case['description'] else "No description provided")
    
    # Participants
    st.subheader("Participants")
    participants = case.get("participants", [])
    
    if participants:
        participant_data = []
        for p in participants:
            participant_data.append({
                "ID": p["id"],
                "Name": p["name"],
                "Role": p["role"].replace("_", " ").title()
            })
            
        st.dataframe(pd.DataFrame(participant_data))
        
        # Store participants in session state
        st.session_state.participants = {p["id"]: p for p in participants}
    else:
        st.info("No participants found for this case")
    
    # Simulations
    st.subheader("Simulations")
    simulations = get_simulations(case["id"])
    
    # Create New Simulation
    with st.expander("Create New Simulation"):
        with st.form("create_simulation_form"):
            sim_title = st.text_input("Simulation Title")
            sim_type = st.selectbox(
                "Simulation Type",
                options=["examination", "cross_examination", "hearing", "mediation", "trial"]
            )
            
            sim_submitted = st.form_submit_button("Create Simulation")
            
            if sim_submitted and sim_title:
                new_simulation = create_simulation(case["id"], sim_title, sim_type)
                
                if new_simulation:
                    st.success(f"Simulation '{sim_title}' created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create simulation")
    
    # List Simulations
    if simulations:
        simulation_data = []
        for sim in simulations:
            simulation_data.append({
                "ID": sim["id"],
                "Title": sim["title"],
                "Type": sim["conversation_type"].replace("_", " ").title(),
                "Status": sim["status"].title(),
                "Started": sim["started_at"]
            })
            
        sim_df = pd.DataFrame(simulation_data)
        st.dataframe(sim_df)
        
        # Select simulation to view
        sim_ids = [sim["id"] for sim in simulations]
        sim_titles = [sim["title"] for sim in simulations]
        
        selected_sim_idx = st.selectbox(
            "Select a simulation to view",
            options=range(len(sim_titles)),
            format_func=lambda i: sim_titles[i]
        )
        
        if st.button("Enter Simulation"):
            selected_sim_id = sim_ids[selected_sim_idx]
            for sim in simulations:
                if sim["id"] == selected_sim_id:
                    st.session_state.current_simulation = sim
                    st.session_state.page = "simulation"
                    st.rerun()
    else:
        st.info("No simulations found for this case")
    
    # Documents
    st.subheader("Documents")
    documents = [d for d in case.get("documents", [])]
    
    if documents:
        doc_data = []
        for doc in documents:
            doc_data.append({
                "ID": doc["id"],
                "Title": doc["title"],
                "Type": doc["document_type"].replace("_", " ").title(),
                "Uploaded": doc["uploaded_at"]
            })
            
        st.dataframe(pd.DataFrame(doc_data))
        
        # Store documents in session state
        st.session_state.documents = documents
    else:
        st.info("No documents found for this case")

def simulation_page():
    """Render the simulation page"""
    simulation = st.session_state.current_simulation
    if not simulation:
        st.error("No simulation selected")
        return
        
    st.header(f"Simulation: {simulation['title']}")
    st.subheader(f"Type: {simulation['conversation_type'].replace('_', ' ').title()}")
    
    # Chat messages
    st.subheader("Courtroom Exchange")
    
    # Get messages for this simulation
    messages = get_simulation_messages(simulation["id"])
    if messages:
        for msg in messages:
            with st.chat_message(msg["participant_role"]):
                st.write(f"**{msg['participant_name']}:** {msg['content']}")
        
        # Store messages in session state
        st.session_state.chat_messages = messages
    
    # Scenario section
    with st.expander("Run Scenario"):
        scenario = st.text_area("Scenario Description", 
                                value="The court is now in session. The judge has called both parties to present their initial statements.")
        
        # Get participants for speaking order
        case = st.session_state.current_case
        participants = case.get("participants", [])
        
        participant_roles = [p["role"] for p in participants]
        
        # Default speaking order: judge, client_counsel, client, opposing_counsel, opposing_party
        default_order = [r for r in ["judge", "client_counsel", "client", "opposing_counsel", "opposing_party"] 
                         if r in participant_roles]
        
        # Allow customization of speaking order
        st.write("Select Speaking Order:")
        speaking_order = []
        for i in range(min(5, len(participants))):
            role_options = [p["role"] for p in participants if p["role"] not in speaking_order]
            if role_options:
                selected_role = st.selectbox(
                    f"Speaker {i+1}",
                    options=role_options,
                    index=min(i, len(role_options)-1),
                    key=f"speaker_{i}"
                )
                speaking_order.append(selected_role)
        
        if st.button("Run Scenario"):
            with st.spinner("Simulating courtroom exchange..."):
                result = run_simulation_scenario(simulation["id"], scenario, speaking_order)
                
                if result:
                    st.success("Scenario completed successfully!")
                    st.rerun()
                else:
                    st.error("Failed to run scenario")
    
    # Single message section
    st.subheader("Send Individual Message")
    
    # Select participant
    participant_options = {f"{p['name']} ({p['role']})": p["id"] for p in case.get("participants", [])}
    
    if participant_options:
        selected_participant = st.selectbox(
            "Select Participant",
            options=list(participant_options.keys())
        )
        
        selected_participant_id = participant_options[selected_participant]
        
        # Message input
        message = st.text_area("Message")
        
        if st.button("Send Message") and message:
            with st.spinner("Sending message..."):
                result = send_message(simulation["id"], selected_participant_id, message)
                
                if result:
                    st.success("Message sent successfully!")
                    st.rerun()
                else:
                    st.error("Failed to send message")
    else:
        st.info("No participants available to send messages")

def upload_document_page():
    """Render the upload document page"""
    st.header("Upload Document")
    
    if not st.session_state.current_case:
        st.error("Please select a case first")
        return
    
    case = st.session_state.current_case
    
    with st.form("upload_document_form"):
        title = st.text_input("Document Title")
        document_type = st.selectbox(
            "Document Type",
            options=["evidence", "affidavit", "legal_brief", "court_filing", "precedent", "testimony"]
        )
        uploaded_file = st.file_uploader("Upload File", type=["pdf", "docx", "txt"])
        
        submitted = st.form_submit_button("Upload Document")
        
        if submitted and title and uploaded_file:
            with st.spinner("Uploading document..."):
                result = upload_document(case["id"], title, document_type, uploaded_file)
                
                if result:
                    st.success(f"Document '{title}' uploaded successfully!")
                    
                    # Update case information
                    st.session_state.current_case = get_case(case["id"])
                    
                    # Ask if user wants to analyze the document
                    if st.button("Analyze Document"):
                        st.session_state.page = "analyze_document"
                        st.session_state.document_to_analyze = result
                        st.rerun()
                else:
                    st.error("Failed to upload document")

def view_documents_page():
    """Render the view documents page"""
    st.header("Case Documents")
    
    if not st.session_state.current_case:
        st.error("Please select a case first")
        return
    
    case = st.session_state.current_case
    documents = [d for d in case.get("documents", [])]
    
    if documents:
        for doc in documents:
            with st.expander(f"{doc['title']} ({doc['document_type']})"):
                st.write(f"**Type:** {doc['document_type'].replace('_', ' ').title()}")
                st.write(f"**Uploaded:** {doc['uploaded_at']}")
                
                if st.button(f"Analyze Document {doc['id']}", key=f"analyze_{doc['id']}"):
                    st.session_state.page = "analyze_document"
                    st.session_state.document_to_analyze = doc
                    st.rerun()
    else:
        st.info("No documents found for this case")

def analyze_document_page():
    """Render the analyze document page"""
    st.header("Document Analysis")
    
    if not hasattr(st.session_state, "document_to_analyze"):
        st.error("No document selected for analysis")
        return
    
    document = st.session_state.document_to_analyze
    
    st.subheader(f"Analyzing: {document['title']}")
    
    analysis_type = st.selectbox(
        "Analysis Type",
        options=["standard", "detailed", "summary"]
    )
    
    if st.button("Start Analysis"):
        with st.spinner("Analyzing document..."):
            result = analyze_document(document["id"], analysis_type)
            
            if result:
                st.success("Analysis completed!")
                
                st.subheader("Analysis Results")
                st.write(result["analysis_result"]["full_analysis"])
                
                st.subheader("Key Points")
                for point in result["key_points"]:
                    st.write(f"• {point}")
            else:
                st.error("Failed to analyze document")

def predict_outcome_page():
    """Render the predict outcome page"""
    st.header("Predict Case Outcome")
    
    if not st.session_state.current_case:
        st.error("Please select a case first")
        return
        
    if not st.session_state.current_simulation:
        st.error("Please select a simulation first")
        return
    
    case = st.session_state.current_case
    simulation = st.session_state.current_simulation
    
    st.subheader(f"Case: {case['title']}")
    st.subheader(f"Simulation: {simulation['title']}")
    
    scenario_description = st.text_area(
        "Scenario Description",
        value=f"Based on the proceedings in the {case['case_type']} court case involving {case['json_data'].get('client_name', 'the client')} and {case['json_data'].get('opposing_name', 'the opposing party')}."
    )
    
    # Factors that might influence the case
    st.subheader("Key Factors")
    
    factors = []
    
    # Default factors for family court
    if case['case_type'] == 'family':
        default_factors = [
            {"name": "Child Welfare", "description": "The best interests of any children involved"},
            {"name": "Financial Stability", "description": "Financial resources and stability of each party"},
            {"name": "Parenting History", "description": "Past involvement and capability of each parent"},
            {"name": "Living Situation", "description": "Housing and living conditions of each party"}
        ]
    else:
        default_factors = [
            {"name": "Evidence Strength", "description": "Strength and admissibility of presented evidence"},
            {"name": "Legal Precedent", "description": "Relevant case law and precedents"},
            {"name": "Witness Credibility", "description": "Credibility and consistency of witness testimony"}
        ]
    
    # Allow editing of factors
    for i, factor in enumerate(default_factors):
        col1, col2 = st.columns([1, 3])
        with col1:
            factor_name = st.text_input(f"Factor {i+1} Name", value=factor["name"], key=f"factor_name_{i}")
        with col2:
            factor_desc = st.text_input(f"Description", value=factor["description"], key=f"factor_desc_{i}")
        
        if factor_name and factor_desc:
            factors.append({"name": factor_name, "description": factor_desc})
    
    # Add custom factor
    with st.expander("Add Custom Factor"):
        col1, col2 = st.columns([1, 3])
        with col1:
            custom_name = st.text_input("Factor Name")
        with col2:
            custom_desc = st.text_input("Description")
        
        if custom_name and custom_desc and st.button("Add Factor"):
            factors.append({"name": custom_name, "description": custom_desc})
            st.rerun()
    
    # Focus areas
    focus_areas = st.multiselect(
        "Focus Areas",
        options=["Legal Merits", "Procedural Issues", "Evidence Weight", "Remedy Appropriateness"]
    )
    
    if st.button("Predict Outcome"):
        with st.spinner("Analyzing case and predicting outcome..."):
            result = predict_outcome(
                simulation["id"],
                case["id"],
                scenario_description,
                factors
            )
            
            if result:
                st.success("Prediction completed!")
                
                # Display prediction
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.metric("Likelihood of Success", f"{int(result['likelihood'] * 100)}%")
                    
                    st.subheader("Key Factors")
                    for factor in result["key_factors"]:
                        impact_color = "green" if factor["impact"] == "positive" else "red"
                        st.markdown(f"• {factor['name']} - <span style='color:{impact_color}'>{factor['impact'].title()}</span> ({factor['weight'].title()} weight)", unsafe_allow_html=True)
                
                with col2:
                    st.subheader("Rationale")
                    st.write(result["rationale"])
                
                st.subheader("Recommendations")
                for rec in result["recommendations"]:
                    st.write(f"• {rec}")
            else:
                st.error("Failed to predict outcome")

# Main Application
def main():
    """Main application function"""
    render_header()
    render_sidebar()
    
    # Default to welcome page
    if "page" not in st.session_state:
        st.session_state.page = "welcome"
    
    # Page router
    if st.session_state.page == "welcome":
        st.header("Welcome to Legal AI Virtual Courtroom")
        st.write("""
        This platform allows you to simulate legal proceedings using AI agents that represent different parties in a case.
        
        To get started:
        1. Create a new case or select an existing one
        2. Upload relevant legal documents
        3. Enter a simulation to interact with AI legal agents
        4. Run scenarios to see how different arguments might play out
        5. Get predictions on potential case outcomes
        
        Use the sidebar to navigate through the application.
        """)
        
        # Quick start
        if st.button("Create New Case"):
            st.session_state.page = "create_case"
            st.rerun()
            
    elif st.session_state.page == "create_case":
        create_case_page()
    elif st.session_state.page == "view_case":
        view_case_page()
    elif st.session_state.page == "simulation":
        simulation_page()
    elif st.session_state.page == "upload_document":
        upload_document_page()
    elif st.session_state.page == "view_documents":
        view_documents_page()
    elif st.session_state.page == "analyze_document":
        analyze_document_page()
    elif st.session_state.page == "predict_outcome":
        predict_outcome_page()

if __name__ == "__main__":
    main()
