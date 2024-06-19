## Customer InsurAssist

Customer InsurAssist is an application designed to facilitate customer interactions related to Cigna insurance products. It leverages various tools and APIs to provide comprehensive information and support to users.

### Overview

Customer InsurAssist integrates with Cigna's FHIR-based APIs and utilizes advanced AI models to assist users with inquiries related to insurance coverage, healthcare provider details, and more. The application supports multiple functionalities through a structured approach using LangChain and other tools.

### Features

- **Integration with Cigna APIs**: Accesses Cigna's APIs to fetch subscriber details, coverage benefits, encounter histories, and more securely using OAuth2 authentication.
  
- **AI-powered Assistance**: Utilizes ChatOpenAI model (GPT-4) to interpret user queries and provide relevant responses using a defined state machine (StateGraph).

- **Toolset**: Includes tools such as `get_person_details`, `get_coverage_details`, `get_plan_information`, `get_explanation_of_benefit`, `get_encounters`, and `get_doctors` to fetch specific information based on user queries.

- **Advanced Retrieval**: Employs SelfQueryRetriever to retrieve relevant documents from a PineconeVectorStore based on user queries about Cigna insurance plans.

### Tech Stack

- **LangChain**: Framework for building AI-driven applications, facilitating integration with different tools and models.
  
- **Streamlit**: Front-end framework for interactive Python applications, used to create the user interface for Customer InsurAssist.

- **OAuth2**: Handles authentication with Cigna's APIs securely to ensure data privacy and access control.

### Setup

1. **Environment Setup**:
   - Ensure `CIGNA_CLIENT_ID` and `CIGNA_CLIENT_SECRET` environment variables are set for authentication.
   - Provide `TAVILY_API_KEY` and `OPENAI_API_KEY` for additional tool functionalities if required.

2. **Dependencies**:
   - Install dependencies using `pip install -r requirements.txt`.

3. **Running the Application**:
   - Launch the application with `streamlit run app.py`.

### Usage

1. **Authentication**:
   - Users authenticate using their Cigna credentials via OAuth2 for secure access to insurance-related information.

2. **Chat Interface**:
   - Users interact with a chat interface to ask questions regarding insurance coverage, healthcare providers, and other related queries.

3. **Response Handling**:
   - The application processes user queries using AI models and fetches relevant information using the integrated toolset based on the type of inquiry.

4. **Persistent Storage**:
   - Utilizes SQLite for storing application state and chat history temporarily during the session.

### Additional Notes

- Ensure sensitive data handling and secure token management to maintain data integrity and user privacy.
- Customize and extend the application based on specific business requirements or additional functionality needs.

This README provides an overview of Customer InsurAssist, its features, setup instructions, and usage guidelines, enabling users and developers to effectively deploy and utilize the application for insurance-related customer interactions. Adjustments can be made based on deployment environments and specific use cases.
