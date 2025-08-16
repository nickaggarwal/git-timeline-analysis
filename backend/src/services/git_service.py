import os
import shutil
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import git
from git import Repo, Commit
import logging
from src.models.schema import CommitHistory, Developer, Branch, Codebase

logger = logging.getLogger(__name__)


class GitService:
    def __init__(self):
        self.temp_dir = None
        self.repo = None
    
    def clone_repository(self, git_url: str, local_path: Optional[str] = None) -> str:
        """Clone a git repository to local storage"""
        try:
            if local_path is None:
                self.temp_dir = tempfile.mkdtemp()
                local_path = self.temp_dir
            
            logger.info(f"Cloning repository {git_url} to {local_path}")
            self.repo = Repo.clone_from(git_url, local_path)
            return local_path
        except Exception as e:
            logger.error(f"Failed to clone repository {git_url}: {str(e)}")
            raise
    
    def get_codebase_info(self, git_url: str) -> Codebase:
        """Extract basic codebase information"""
        if not self.repo:
            raise ValueError("Repository not cloned. Call clone_repository first.")
        
        # Get repository name from URL
        repo_name = git_url.split('/')[-1].replace('.git', '')
        
        # Get total commits
        total_commits = sum(1 for _ in self.repo.iter_commits('--all'))
        
        # Get unique developers
        developers = set()
        for commit in self.repo.iter_commits('--all'):
            developers.add(commit.author.email)
        
        # Get primary language (simplified - based on file extensions)
        primary_language = self._get_primary_language()
        
        return Codebase(
            id=repo_name,
            git_url=git_url,
            name=repo_name,
            created_at=datetime.now(),
            total_commits=total_commits,
            total_developers=len(developers),
            primary_language=primary_language
        )
    
    def get_all_branches(self) -> List[Branch]:
        """Get all branches in the repository"""
        if not self.repo:
            raise ValueError("Repository not cloned. Call clone_repository first.")
        
        branches = []
        for branch in self.repo.heads:
            branch_info = Branch(
                id=f"{self.repo.working_dir}_{branch.name}",
                name=branch.name,
                codebase_id=os.path.basename(self.repo.working_dir),
                created_at=datetime.now(),  # Could be improved with actual creation date
                last_commit_sha=branch.commit.hexsha,
                is_main_branch=branch.name in ['main', 'master'],
                total_commits=sum(1 for _ in self.repo.iter_commits(branch.name))
            )
            branches.append(branch_info)
        
        return branches
    
    def get_commit_history(self, branch: str = None, max_count: int = None) -> List[CommitHistory]:
        """Extract detailed commit history"""
        if not self.repo:
            raise ValueError("Repository not cloned. Call clone_repository first.")
        
        commits = []
        commit_iter = self.repo.iter_commits(branch or '--all', max_count=max_count)
        
        for commit in commit_iter:
            try:
                # Get files changed in this commit
                files_changed = []
                insertions = 0
                deletions = 0
                
                if commit.parents:  # Not the initial commit
                    diffs = commit.parents[0].diff(commit, create_patch=True)
                    for diff in diffs:
                        if diff.a_path:
                            files_changed.append(diff.a_path)
                        if diff.b_path and diff.b_path not in files_changed:
                            files_changed.append(diff.b_path)
                    
                    # Get insertions/deletions (approximation)
                    stats = commit.stats.total
                    insertions = stats['insertions']
                    deletions = stats['deletions']
                
                commit_history = CommitHistory(
                    id=commit.hexsha,
                    sha=commit.hexsha,
                    message=commit.message.strip(),
                    author_name=commit.author.name,
                    author_email=commit.author.email,
                    committer_name=commit.committer.name,
                    committer_email=commit.committer.email,
                    timestamp=datetime.fromtimestamp(commit.committed_date),
                    branch=branch or "unknown",
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions,
                    parent_shas=[parent.hexsha for parent in commit.parents],
                    complexity_score=self._calculate_complexity_score(insertions, deletions, len(files_changed))
                )
                commits.append(commit_history)
                
            except Exception as e:
                logger.warning(f"Failed to process commit {commit.hexsha}: {str(e)}")
                continue
        
        return commits
    
    def get_developers(self) -> List[Developer]:
        """Extract developer information from commit history"""
        if not self.repo:
            raise ValueError("Repository not cloned. Call clone_repository first.")
        
        developer_stats = {}
        
        for commit in self.repo.iter_commits('--all'):
            email = commit.author.email
            name = commit.author.name
            commit_date = datetime.fromtimestamp(commit.committed_date)
            
            if email not in developer_stats:
                developer_stats[email] = {
                    'name': name,
                    'email': email,
                    'commits': [],
                    'files': set(),
                    'lines_added': 0,
                    'lines_removed': 0
                }
            
            dev_data = developer_stats[email]
            dev_data['commits'].append(commit_date)
            
            # Get file changes and line stats for this commit
            if commit.parents:
                stats = commit.stats.total
                dev_data['lines_added'] += stats['insertions']
                dev_data['lines_removed'] += stats['deletions']
                
                # Track files touched
                for file_path, file_stats in commit.stats.files.items():
                    dev_data['files'].add(file_path)
        
        developers = []
        for email, data in developer_stats.items():
            expertise_areas = self._determine_expertise_areas(list(data['files']))
            
            developer = Developer(
                id=email,
                name=data['name'],
                email=email,
                total_commits=len(data['commits']),
                expertise_areas=expertise_areas,
                contribution_score=self._calculate_contribution_score(
                    len(data['commits']), 
                    data['lines_added'], 
                    data['lines_removed'],
                    len(data['files'])
                ),
                first_commit_date=min(data['commits']) if data['commits'] else None,
                last_commit_date=max(data['commits']) if data['commits'] else None,
                lines_added=data['lines_added'],
                lines_removed=data['lines_removed']
            )
            developers.append(developer)
        
        return developers
    
    def _get_primary_language(self) -> Optional[str]:
        """Determine primary programming language based on file extensions"""
        if not self.repo:
            return None
        
        file_extensions = {}
        
        try:
            # Walk through all files in the repository
            for root, dirs, files in os.walk(self.repo.working_dir):
                # Skip .git directory
                if '.git' in root:
                    continue
                
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext:
                        file_extensions[ext] = file_extensions.get(ext, 0) + 1
            
            # Map extensions to languages
            language_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.cs': 'C#',
                '.php': 'PHP',
                '.rb': 'Ruby',
                '.go': 'Go',
                '.rs': 'Rust',
                '.swift': 'Swift',
                '.kt': 'Kotlin'
            }
            
            # Find most common extension
            if file_extensions:
                most_common_ext = max(file_extensions, key=file_extensions.get)
                return language_map.get(most_common_ext, most_common_ext)
        
        except Exception as e:
            logger.warning(f"Failed to determine primary language: {str(e)}")
        
        return None
    
    def _calculate_complexity_score(self, insertions: int, deletions: int, files_changed: int) -> float:
        """Calculate a simple complexity score for a commit"""
        # Simple heuristic: more changes = higher complexity
        total_changes = insertions + deletions
        file_factor = files_changed * 0.5
        return min(total_changes * 0.1 + file_factor, 10.0)  # Cap at 10
    
    def _determine_expertise_areas(self, files: List[str]) -> List[str]:
        """Determine expertise areas based on file patterns"""
        areas = set()
        
        for file_path in files:
            file_lower = file_path.lower()
            
            # Frontend
            if any(ext in file_path for ext in ['.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css', '.scss']):
                areas.add('Frontend')
            
            # Backend
            if any(ext in file_path for ext in ['.py', '.java', '.go', '.php', '.rb', '.cs']):
                areas.add('Backend')
            
            # Database
            if any(keyword in file_lower for keyword in ['migration', 'schema', '.sql', 'database']):
                areas.add('Database')
            
            # DevOps
            if any(keyword in file_lower for keyword in ['dockerfile', 'docker-compose', '.yml', '.yaml', 'jenkins', 'ci']):
                areas.add('DevOps')
            
            # Testing
            if any(keyword in file_lower for keyword in ['test', 'spec', '__test__']):
                areas.add('Testing')
            
            # Documentation
            if any(ext in file_path for ext in ['.md', '.rst', '.txt']):
                areas.add('Documentation')
        
        return list(areas) if areas else ['General']
    
    def _calculate_contribution_score(self, commits: int, lines_added: int, lines_removed: int, files_touched: int) -> float:
        """Calculate a contribution score for a developer"""
        # Weighted scoring system
        commit_score = commits * 2
        line_score = (lines_added + lines_removed) * 0.01
        file_score = files_touched * 0.5
        
        return round(commit_score + line_score + file_score, 2)
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
        self.repo = None