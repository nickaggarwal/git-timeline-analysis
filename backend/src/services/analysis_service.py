from openai import OpenAI, AzureOpenAI
import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import re
import json
from src.models.schema import CommitHistory, Developer, BusinessMilestone

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.client = None
        self.use_azure = os.getenv('USE_AZURE_OPENAI', 'false').lower() == 'true'
        
        if self.use_azure:
            # Initialize Azure OpenAI client
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            azure_key = os.getenv('AZURE_OPENAI_API_KEY')
            azure_version = os.getenv('AZURE_OPENAI_API_VERSION')
            
            if azure_endpoint and azure_key:
                self.client = AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=azure_version
                )
                self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-35-turbo')
                logger.info("Initialized Azure OpenAI client")
            else:
                logger.warning("Azure OpenAI configuration missing")
        elif openai_api_key:
            # Use regular OpenAI
            self.client = OpenAI(api_key=openai_api_key)
            self.deployment_name = "gpt-3.5-turbo"
            logger.info("Initialized OpenAI client")
        else:
            logger.info("No LLM client configured - using basic analysis only")
    
    def analyze_commit_patterns(self, commits: List[CommitHistory]) -> Dict[str, Any]:
        """Analyze patterns in commit history"""
        if not commits:
            return {}
        
        analysis = {
            'total_commits': len(commits),
            'date_range': {
                'start': min(commit.timestamp for commit in commits),
                'end': max(commit.timestamp for commit in commits)
            },
            'activity_by_day': {},
            'activity_by_hour': {},
            'commit_frequency': {},
            'file_change_patterns': {},
            'commit_size_distribution': {},
            'developer_activity': {}
        }
        
        # Analyze temporal patterns
        for commit in commits:
            day_name = commit.timestamp.strftime('%A')
            hour = commit.timestamp.hour
            
            analysis['activity_by_day'][day_name] = analysis['activity_by_day'].get(day_name, 0) + 1
            analysis['activity_by_hour'][hour] = analysis['activity_by_hour'].get(hour, 0) + 1
            
            # Developer activity
            dev_email = commit.author_email
            if dev_email not in analysis['developer_activity']:
                analysis['developer_activity'][dev_email] = {
                    'commits': 0,
                    'total_changes': 0,
                    'files_touched': set()
                }
            
            analysis['developer_activity'][dev_email]['commits'] += 1
            analysis['developer_activity'][dev_email]['total_changes'] += commit.insertions + commit.deletions
            analysis['developer_activity'][dev_email]['files_touched'].update(commit.files_changed)
            
            # Commit size distribution
            total_changes = commit.insertions + commit.deletions
            if total_changes < 10:
                size_category = 'small'
            elif total_changes < 100:
                size_category = 'medium'
            elif total_changes < 500:
                size_category = 'large'
            else:
                size_category = 'huge'
            
            analysis['commit_size_distribution'][size_category] = analysis['commit_size_distribution'].get(size_category, 0) + 1
        
        # Convert sets to lists for JSON serialization
        for dev_data in analysis['developer_activity'].values():
            dev_data['files_touched'] = list(dev_data['files_touched'])
        
        return analysis
    
    def generate_feature_summary(self, commit: CommitHistory) -> Optional[str]:
        """Generate an LLM-powered feature summary for a commit"""
        if not self.client:
            return self._generate_basic_summary(commit)
        
        try:
            prompt = self._create_commit_analysis_prompt(commit)
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Analyze git commits and provide concise feature summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Failed to generate LLM summary for commit {commit.sha}: {str(e)}")
            return self._generate_basic_summary(commit)
    
    def analyze_business_impact(self, commit: CommitHistory) -> Optional[str]:
        """Analyze the business impact of a commit using LLM"""
        if not self.client:
            return None
        
        try:
            prompt = f"""
            Analyze this git commit for business impact:
            
            Message: {commit.message}
            Files changed: {', '.join(commit.files_changed[:10])}
            Lines added/removed: +{commit.insertions}/-{commit.deletions}
            
            Categorize the business impact as one of:
            - Feature: New functionality
            - Enhancement: Improvement to existing feature
            - Bug Fix: Error correction
            - Refactoring: Code improvement without functional change
            - Infrastructure: Build, deployment, or tooling changes
            - Documentation: Documentation updates
            - Security: Security-related changes
            - Performance: Performance optimizations
            
            Provide a brief explanation (1-2 sentences) of why this categorization was chosen.
            
            Format: "Category: Brief explanation"
            """
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a business analyst who understands software development impacts."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Failed to analyze business impact for commit {commit.sha}: {str(e)}")
            return None
    
    def identify_business_milestones(self, commits: List[CommitHistory], codebase_id: str) -> List[BusinessMilestone]:
        """Identify potential business milestones from commit history"""
        milestones = []
        
        # Look for version tags, release commits, and major feature merges
        milestone_patterns = [
            (r'v?\d+\.\d+\.\d+', 'release'),  # Version numbers
            (r'release|deploy|launch', 'release'),
            (r'merge.*feature|feat.*merge', 'feature'),
            (r'hotfix|critical|urgent', 'bugfix'),
            (r'initial.*commit|first.*commit', 'initialization')
        ]
        
        for commit in commits:
            message_lower = commit.message.lower()
            
            for pattern, milestone_type in milestone_patterns:
                if re.search(pattern, message_lower):
                    # Extract version if it's a release
                    version = None
                    if milestone_type == 'release':
                        version_match = re.search(r'v?(\d+\.\d+\.\d+)', commit.message)
                        if version_match:
                            version = version_match.group(1)
                    
                    milestone = BusinessMilestone(
                        id=f"{codebase_id}_{commit.sha[:8]}",
                        name=commit.message.split('\n')[0][:100],  # First line, truncated
                        description=commit.message,
                        date=commit.timestamp,
                        codebase_id=codebase_id,
                        related_commits=[commit.sha],
                        milestone_type=milestone_type,
                        version=version
                    )
                    milestones.append(milestone)
                    break  # Only one milestone type per commit
        
        return milestones
    
    def analyze_developer_expertise(self, developer: Developer, commits: List[CommitHistory]) -> Dict[str, Any]:
        """Analyze developer expertise based on their commits"""
        dev_commits = [c for c in commits if c.author_email == developer.email]
        
        if not dev_commits:
            return {}
        
        expertise_analysis = {
            'primary_areas': developer.expertise_areas,
            'commit_patterns': {
                'avg_commit_size': sum(c.insertions + c.deletions for c in dev_commits) / len(dev_commits),
                'commit_frequency': len(dev_commits),
                'preferred_hours': {},
                'preferred_days': {}
            },
            'code_quality_indicators': {
                'avg_files_per_commit': sum(len(c.files_changed) for c in dev_commits) / len(dev_commits),
                'commit_message_quality': self._analyze_commit_message_quality(dev_commits)
            },
            'collaboration_patterns': {
                'files_commonly_changed': self._find_common_files(dev_commits),
                'potential_conflicts': []
            }
        }
        
        # Analyze temporal patterns
        for commit in dev_commits:
            hour = commit.timestamp.hour
            day = commit.timestamp.strftime('%A')
            
            expertise_analysis['commit_patterns']['preferred_hours'][hour] = \
                expertise_analysis['commit_patterns']['preferred_hours'].get(hour, 0) + 1
            expertise_analysis['commit_patterns']['preferred_days'][day] = \
                expertise_analysis['commit_patterns']['preferred_days'].get(day, 0) + 1
        
        return expertise_analysis
    
    def _create_commit_analysis_prompt(self, commit: CommitHistory) -> str:
        """Create a prompt for LLM commit analysis"""
        return f"""
        Analyze this git commit and provide a concise feature summary:
        
        Commit Message: {commit.message}
        Files Changed: {', '.join(commit.files_changed[:10])}
        Insertions: {commit.insertions}
        Deletions: {commit.deletions}
        Author: {commit.author_name}
        
        Provide a 1-2 sentence summary of what this commit accomplishes in terms of features or functionality.
        Focus on the business value and user-facing changes.
        """
    
    def _generate_basic_summary(self, commit: CommitHistory) -> str:
        """Generate a basic summary without LLM"""
        message_parts = commit.message.split('\n')[0].lower()
        
        if any(keyword in message_parts for keyword in ['add', 'implement', 'create']):
            return f"Added new functionality: {commit.message.split()[0:10]}"
        elif any(keyword in message_parts for keyword in ['fix', 'resolve', 'bug']):
            return f"Bug fix: {commit.message.split()[0:10]}"
        elif any(keyword in message_parts for keyword in ['update', 'modify', 'change']):
            return f"Updated existing feature: {commit.message.split()[0:10]}"
        elif any(keyword in message_parts for keyword in ['refactor', 'cleanup', 'improve']):
            return f"Code improvement: {commit.message.split()[0:10]}"
        else:
            return f"General change: {commit.message.split()[0:10]}"
    
    def _analyze_commit_message_quality(self, commits: List[CommitHistory]) -> float:
        """Analyze the quality of commit messages"""
        if not commits:
            return 0.0
        
        quality_score = 0.0
        
        for commit in commits:
            message = commit.message.strip()
            score = 0.0
            
            # Length check (not too short, not too long)
            if 10 <= len(message) <= 200:
                score += 0.3
            
            # Starts with capital letter
            if message and message[0].isupper():
                score += 0.2
            
            # Contains meaningful words
            meaningful_words = ['add', 'fix', 'update', 'implement', 'refactor', 'improve']
            if any(word in message.lower() for word in meaningful_words):
                score += 0.3
            
            # Not generic
            generic_messages = ['wip', 'temp', 'fix', 'update', 'changes']
            if message.lower() not in generic_messages:
                score += 0.2
            
            quality_score += score
        
        return round(quality_score / len(commits), 2)
    
    def _find_common_files(self, commits: List[CommitHistory]) -> List[str]:
        """Find files that are commonly changed by a developer"""
        file_counts = {}
        
        for commit in commits:
            for file_path in commit.files_changed:
                file_counts[file_path] = file_counts.get(file_path, 0) + 1
        
        # Return files changed more than once, sorted by frequency
        common_files = [(file, count) for file, count in file_counts.items() if count > 1]
        common_files.sort(key=lambda x: x[1], reverse=True)
        
        return [file for file, count in common_files[:10]]  # Top 10