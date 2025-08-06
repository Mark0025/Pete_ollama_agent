"""
LangChain Research Agent for Ollama Modelfile Best Practices
"""

import os
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# LangChain imports
from langchain.agents import AgentType, initialize_agent
from langchain_ollama import OllamaLLM
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)

class OllamaResearchAgent:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.search_tool = DuckDuckGoSearchRun()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize Ollama LLM
        self.llm = OllamaLLM(
            base_url=ollama_host,
            model="llama3:latest",
            temperature=0.7
        )
        
        # Initialize agent with search tools
        self.tools = [self.search_tool]
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
        
        self.research_findings = {}
        self.existing_files_analysis = {}

    def research_ollama_best_practices(self) -> Dict[str, Any]:
        """
        Research Ollama best practices from multiple sources
        """
        logger.info("🔍 Starting Ollama Modelfile research...")
        
        research_queries = [
            "NetworkChuck Ollama tutorial best practices",
            "Ollama Modelfile documentation official guide",
            "GitHub Ollama custom model examples",
            "Ollama MODEL MESSAGE training examples best practices",
            "Ollama fine-tuning conversation data tips",
            "Ollama system prompt optimization techniques",
            "Ollama parameter tuning temperature top_p best values"
        ]
        
        findings = {}
        
        for query in research_queries:
            logger.info(f"🔎 Researching: {query}")
            try:
                search_results = self.search_tool.run(query)
                
                # Ask agent to analyze the search results
                analysis_prompt = f"""
                Analyze these search results about Ollama best practices and extract key insights:
                
                Query: {query}
                Results: {search_results}
                
                Please extract:
                1. Key best practices mentioned
                2. Specific Modelfile structure recommendations
                3. Parameter optimization tips
                4. Common mistakes to avoid
                5. Example implementations
                
                Focus on actionable insights for building effective Modelfiles with conversation data.
                """
                
                analysis = self.agent.run(analysis_prompt)
                findings[query] = {
                    "raw_results": search_results,
                    "analysis": analysis
                }
                
            except Exception as e:
                logger.error(f"Error researching {query}: {e}")
                findings[query] = {"error": str(e)}
        
        self.research_findings = findings
        return findings

    def analyze_existing_project_files(self, project_root: str = "/Users/markcarpenter/Desktop/pete/ollama_agent") -> Dict[str, Any]:
        """
        Analyze our existing Modelfiles and logs to understand current problems
        """
        logger.info("📁 Analyzing existing project files and logs...")
        
        analysis = {
            "modelfiles": {},
            "logs": {},
            "problems_identified": [],
            "patterns_found": []
        }
        
        # Find and analyze all Modelfiles
        models_dir = Path(project_root) / "models"
        if models_dir.exists():
            for modelfile in models_dir.glob("Modelfile*"):
                try:
                    with open(modelfile, 'r') as f:
                        content = f.read()
                    
                    analysis_prompt = f"""
                    Analyze this Modelfile and identify issues that might cause:
                    1. Conversation loops or repetitive responses
                    2. Back-and-forth conversation simulation instead of single responses
                    3. Poor response quality or off-topic responses
                    4. Syntax errors or structural problems
                    
                    Modelfile ({modelfile.name}):
                    {content}
                    
                    Provide specific analysis of problems and suggestions for improvement.
                    """
                    
                    file_analysis = self.agent.run(analysis_prompt)
                    analysis["modelfiles"][modelfile.name] = {
                        "content": content,
                        "analysis": file_analysis,
                        "size": len(content)
                    }
                    
                except Exception as e:
                    logger.error(f"Error analyzing {modelfile}: {e}")
                    analysis["modelfiles"][modelfile.name] = {"error": str(e)}
        
        # Find and analyze log files
        logs_dir = Path(project_root) / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                    
                    # Analyze last 2000 characters for recent issues
                    recent_content = content[-2000:] if len(content) > 2000 else content
                    
                    log_analysis_prompt = f"""
                    Analyze these recent log entries to identify issues with our Ollama models:
                    
                    Log file ({log_file.name}):
                    {recent_content}
                    
                    Look for:
                    1. Model creation errors
                    2. Response quality issues
                    3. Training problems
                    4. Performance issues
                    
                    What problems can you identify?
                    """
                    
                    log_analysis = self.agent.run(log_analysis_prompt)
                    analysis["logs"][log_file.name] = {
                        "analysis": log_analysis,
                        "size": len(content)
                    }
                    
                except Exception as e:
                    logger.error(f"Error analyzing {log_file}: {e}")
                    analysis["logs"][log_file.name] = {"error": str(e)}
        
        # Look for specific problem patterns in concatenated output
        concat_file = Path(project_root) / "concatenated_output.txt"
        if concat_file.exists():
            try:
                with open(concat_file, 'r') as f:
                    content = f.read()
                
                problem_analysis_prompt = f"""
                This file contains outputs from our previous model attempts. Analyze it to understand what went wrong:
                
                File content (first 3000 chars):
                {content[:3000]}
                
                Identify specific problems:
                1. Why might responses be repetitive or looping?
                2. What patterns suggest conversation simulation vs single responses?
                3. What indicates poor training data formatting?
                4. What Ollama-specific issues can you spot?
                """
                
                problem_analysis = self.agent.run(problem_analysis_prompt)
                analysis["problems_identified"].append(problem_analysis)
                
            except Exception as e:
                logger.error(f"Error analyzing concatenated output: {e}")
        
        self.existing_files_analysis = analysis
        return analysis

    def synthesize_modelfile_guidelines(self) -> Dict[str, Any]:
        """
        Synthesize research findings and existing file analysis into actionable Modelfile guidelines
        """
        logger.info("🧠 Synthesizing research and existing file analysis into Modelfile guidelines...")
        
        synthesis_prompt = f"""
        Based on the following research findings AND analysis of our existing failed attempts, create comprehensive guidelines for building an effective Modelfile for a property management AI trained on conversation data:

        Research Findings:
        {json.dumps(self.research_findings, indent=2)}

        Analysis of Our Existing Files and Problems:
        {json.dumps(self.existing_files_analysis, indent=2)}

        CRITICAL CONTEXT: Our previous attempts have failed because:
        1. The AI simulates conversations instead of responding AS Jamie
        2. Responses loop or become repetitive
        3. Models get stuck in conversation patterns
        4. We need single, focused responses, not back-and-forth dialogue

        Please provide:
        1. SYSTEM prompt best practices specifically addressing our conversation simulation problem
        2. Optimal PARAMETER values to prevent loops and conversation simulation
        3. MESSAGE training example guidelines that avoid conversation patterns
        4. How to format conversation data to train single-response behavior
        5. Best practices for avoiding the specific loops/repetition we've experienced
        6. Template optimization to prevent conversation simulation
        7. Specific recommendations for training Jamie-like responses without dialogue simulation

        Format as a detailed guide with specific examples and recommendations that solve our identified problems.
        """
        
        try:
            guidelines = self.agent.run(synthesis_prompt)
            return {
                "guidelines": guidelines,
                "research_sources": list(self.research_findings.keys())
            }
        except Exception as e:
            logger.error(f"Error synthesizing guidelines: {e}")
            return {"error": str(e)}

    def generate_optimized_modelfile(self, conversation_data: List[Dict], model_name: str) -> str:
        """
        Generate an optimized Modelfile based on research findings
        """
        logger.info("🎯 Generating research-based optimized Modelfile...")
        
        # First get the guidelines
        guidelines = self.synthesize_modelfile_guidelines()
        
        generation_prompt = f"""
        Using the research-based guidelines below, generate an optimized Ollama Modelfile for training an AI to respond EXACTLY like Jamie, a property manager.

        CRITICAL GOAL: We are training an AI to talk exactly like Jamie and respond AS Jamie to any question. The AI should respond like Jamie would, NOT simulate a back-and-forth conversation. When I ask the AI any question, it should respond as Jamie would respond, not act like Jamie AND the client.

        CURRENT PROBLEM: Our existing Modelfile makes the AI act like it's in a conversation with back-and-forth responses, but we want it to simply respond AS Jamie to any single question or statement.

        Guidelines: {guidelines.get('guidelines', 'No guidelines available')}

        Training Data Context:
        - Total conversations: {len(conversation_data)}
        - Data includes: Real property management phone calls between Jamie and tenants
        - Jamie handles: maintenance requests, rent payments, lease issues, emergency repairs
        - Jamie's communication style: Professional, helpful, proactive, empathetic

        SPECIFIC REQUIREMENTS:
        1. Create a SYSTEM prompt that makes the AI respond AS Jamie (not simulate conversations)
        2. Set PARAMETER values that prevent looping and conversation simulation
        3. Use MESSAGE examples where:
           - USER: tenant question/issue
           - ASSISTANT: how Jamie would respond (single response, not conversation)
        4. Avoid any patterns that make the AI think it's having a back-and-forth conversation
        5. Make responses focused, helpful, and in Jamie's professional style
        6. Each response should be complete and actionable, not expecting a reply

        EXAMPLE OF WHAT WE WANT:
        User asks: "My AC is broken"
        AI responds AS Jamie: "I'll get our HVAC contractor out there today. Let me call them now and have them contact you within the hour to schedule a time. Can you confirm your phone number so they can reach you?"

        WHAT WE DON'T WANT:
        - AI simulating both sides of a conversation
        - Responses that expect back-and-forth dialogue
        - Looping or repetitive responses

        Generate the complete Modelfile content following Ollama best practices for single-response training.
        Model name: {model_name}
        """
        
        try:
            modelfile_content = self.agent.run(generation_prompt)
            return modelfile_content
        except Exception as e:
            logger.error(f"Error generating Modelfile: {e}")
            return f"# Error generating Modelfile: {e}"

    def save_research_report(self, output_path: str) -> bool:
        """
        Save research findings and guidelines to file
        """
        try:
            research_report = {
                "research_findings": self.research_findings,
                "guidelines": self.synthesize_modelfile_guidelines(),
                "timestamp": str(Path(__file__).stat().st_mtime)
            }
            
            with open(output_path, 'w') as f:
                json.dump(research_report, f, indent=2)
            
            logger.info(f"✅ Research report saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving research report: {e}")
            return False


def main():
    """Test the research agent"""
    logger.info("🤖 Testing Ollama Research Agent")
    
    agent = OllamaResearchAgent()
    
    # Research best practices
    findings = agent.research_ollama_best_practices()
    
    # Save research report
    report_path = "/Users/markcarpenter/Desktop/pete/ollama_agent/ollama_research_report.json"
    agent.save_research_report(report_path)
    
    logger.info("🎉 Research complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()