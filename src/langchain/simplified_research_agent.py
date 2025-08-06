"""
Simplified Research Agent for Ollama Modelfile Best Practices
"""

import os
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Simplified imports
from langchain_ollama import OllamaLLM
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger(__name__)

class SimplifiedResearchAgent:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.search_tool = DuckDuckGoSearchRun()
        
        # Initialize Ollama LLM
        self.llm = OllamaLLM(
            base_url=ollama_host,
            model="llama3:latest",
            temperature=0.7
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
            "Ollama MESSAGE training examples best practices",
            "Ollama system prompt optimization techniques"
        ]
        
        findings = {}
        
        for query in research_queries:
            logger.info(f"🔎 Researching: {query}")
            try:
                search_results = self.search_tool.run(query)
                
                # Analyze the search results
                analysis_prompt = f"""
                Analyze these search results about Ollama best practices and extract key insights:
                
                Query: {query}
                Results: {search_results}
                
                Extract:
                1. Key best practices mentioned
                2. Specific Modelfile structure recommendations
                3. Parameter optimization tips
                4. Common mistakes to avoid
                5. Example implementations
                
                Focus on actionable insights for building effective Modelfiles with conversation data.
                Provide a concise summary of the most important points.
                """
                
                analysis = self.llm.invoke(analysis_prompt)
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
                    {content[:2000]}...
                    
                    Provide specific analysis of problems and suggestions for improvement.
                    Be concise and actionable.
                    """
                    
                    file_analysis = self.llm.invoke(analysis_prompt)
                    analysis["modelfiles"][modelfile.name] = {
                        "analysis": file_analysis,
                        "size": len(content)
                    }
                    
                except Exception as e:
                    logger.error(f"Error analyzing {modelfile}: {e}")
                    analysis["modelfiles"][modelfile.name] = {"error": str(e)}
        
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
                
                Be specific and actionable in your analysis.
                """
                
                problem_analysis = self.llm.invoke(problem_analysis_prompt)
                analysis["problems_identified"].append(problem_analysis)
                
            except Exception as e:
                logger.error(f"Error analyzing concatenated output: {e}")
        
        self.existing_files_analysis = analysis
        return analysis

    def generate_optimized_modelfile(self, conversation_data: List[Dict], model_name: str) -> str:
        """
        Generate an optimized Modelfile based on research findings and existing file analysis
        """
        logger.info("🎯 Generating research-based optimized Modelfile...")
        
        # Create summary of research and analysis
        research_summary = ""
        for query, data in self.research_findings.items():
            if "analysis" in data:
                research_summary += f"\n{query}: {data['analysis']}\n"
        
        file_analysis_summary = ""
        for filename, data in self.existing_files_analysis.get("modelfiles", {}).items():
            if "analysis" in data:
                file_analysis_summary += f"\n{filename}: {data['analysis']}\n"
        
        problems_summary = "\n".join(self.existing_files_analysis.get("problems_identified", []))
        
        generation_prompt = f"""
        Create an optimized Ollama Modelfile for training an AI to respond EXACTLY like Jamie, a property manager.

        CRITICAL GOAL: Train an AI to respond AS Jamie to any question. The AI should give single, focused responses like Jamie would, NOT simulate conversations.

        CURRENT PROBLEM: Our existing Modelfiles make the AI act like it's in a conversation with back-and-forth responses, but we want it to simply respond AS Jamie to any single question.

        Research Findings Summary:
        {research_summary}

        Analysis of Our Failed Attempts:
        {file_analysis_summary}

        Specific Problems We've Encountered:
        {problems_summary}

        Training Data Context:
        - {len(conversation_data)} real property management phone calls
        - Jamie handles: maintenance, rent, leases, emergency repairs
        - Jamie's style: Professional, helpful, proactive, empathetic

        REQUIREMENTS:
        1. SYSTEM prompt that makes AI respond AS Jamie (not simulate conversations)
        2. PARAMETER values that prevent loops and conversation simulation
        3. MESSAGE examples: USER=tenant issue, ASSISTANT=Jamie's single response
        4. Avoid conversation patterns
        5. Make responses complete and actionable
        6. Each response should be focused, not expecting a reply

        EXAMPLE TARGET BEHAVIOR:
        User: "My AC is broken"
        AI AS Jamie: "I'll get our HVAC contractor out there today. Let me call them now and have them contact you within the hour to schedule a time. Can you confirm your phone number so they can reach you?"

        Generate the complete Modelfile following Ollama syntax.
        Model name: {model_name}
        Include 10-15 carefully selected MESSAGE pairs that demonstrate single-response behavior.
        """
        
        try:
            modelfile_content = self.llm.invoke(generation_prompt)
            return modelfile_content
        except Exception as e:
            logger.error(f"Error generating Modelfile: {e}")
            return f"# Error generating Modelfile: {e}"

    def save_research_report(self, output_path: str) -> bool:
        """
        Save research findings and analysis to file
        """
        try:
            research_report = {
                "research_findings": self.research_findings,
                "existing_files_analysis": self.existing_files_analysis,
                "timestamp": str(Path(__file__).stat().st_mtime)
            }
            
            with open(output_path, 'w') as f:
                json.dump(research_report, f, indent=2)
            
            logger.info(f"✅ Research report saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving research report: {e}")
            return False