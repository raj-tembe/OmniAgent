import subprocess
import time
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Service configuration for integration testing"""
    name: str
    command: str
    port: int
    health_check_url: Optional[str] = None
    startup_timeout: int = 30
    environment: Optional[Dict[str, str]] = None


class IntegrationTestHelper:
    """
    Integration test helper for web applications.
    
    Responsibilities:
    - Start and stop services
    - Health check services
    - Manage test databases
    - Cleanup resources
    """

    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
        self.services: Dict[str, subprocess.Popen] = {}
        self.started_services: List[str] = []

    def start_service(
        self,
        config: ServiceConfig,
        shell: bool = False
    ) -> Tuple[bool, str]:
        """
        Start a service process.
        
        Args:
            config: Service configuration
            shell: Whether to use shell execution
            
        Returns:
            Tuple of (success, message)
        """
        try:
            env = os.environ.copy()
            if config.environment:
                env.update(config.environment)

            process = subprocess.Popen(
                config.command if shell else config.command.split(),
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                shell=shell
            )

            self.services[config.name] = process
            self.started_services.append(config.name)

            # Wait for service to be healthy
            if config.health_check_url:
                healthy = self._wait_for_health(
                    config.health_check_url,
                    config.startup_timeout
                )
                if not healthy:
                    self.stop_service(config.name)
                    return False, f"Service {config.name} failed health check"
            else:
                # Simple wait
                time.sleep(1)

            return True, f"Service {config.name} started successfully"

        except Exception as e:
            return False, f"Error starting service {config.name}: {str(e)}"

    def stop_service(self, service_name: str) -> Tuple[bool, str]:
        """
        Stop a running service.
        
        Args:
            service_name: Name of the service to stop
            
        Returns:
            Tuple of (success, message)
        """
        if service_name not in self.services:
            return False, f"Service {service_name} not found"

        try:
            process = self.services[service_name]
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            del self.services[service_name]
            if service_name in self.started_services:
                self.started_services.remove(service_name)

            return True, f"Service {service_name} stopped successfully"

        except Exception as e:
            return False, f"Error stopping service {service_name}: {str(e)}"

    def stop_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """
        Stop all running services.
        
        Returns:
            Dictionary of service stop results
        """
        results = {}
        for service_name in list(self.services.keys()):
            success, message = self.stop_service(service_name)
            results[service_name] = (success, message)

        return results

    def _wait_for_health(
        self,
        health_url: str,
        max_wait: int = 30
    ) -> bool:
        """
        Wait for service to be healthy.
        
        Args:
            health_url: URL to health check endpoint
            max_wait: Maximum wait time in seconds
            
        Returns:
            True if service becomes healthy
        """
        try:
            import requests
        except ImportError:
            return True  # Skip health check if requests not available

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code < 500:
                    return True
            except (ConnectionError, Exception):
                pass

            time.sleep(0.5)

        return False

    def get_service_status(self) -> Dict[str, Dict]:
        """
        Get status of all services.
        
        Returns:
            Dictionary of service status information
        """
        status = {}
        for name, process in self.services.items():
            status[name] = {
                "running": process.poll() is None,
                "pid": process.pid if process.poll() is None else None
            }

        return status

    @staticmethod
    def setup_test_database(db_config: Dict) -> Dict:
        """
        Setup test database.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Setup result
        """
        db_type = db_config.get("type", "sqlite")

        if db_type == "sqlite":
            db_path = db_config.get("path", "test.db")
            # SQLite databases are created on first connection
            return {
                "success": True,
                "database": db_path,
                "message": "SQLite database ready"
            }

        elif db_type == "postgresql":
            try:
                import psycopg2
                
                conn = psycopg2.connect(
                    host=db_config.get("host", "localhost"),
                    user=db_config.get("user", "postgres"),
                    password=db_config.get("password", ""),
                    database="postgres"
                )
                cursor = conn.cursor()

                db_name = db_config.get("database", "test_db")
                cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
                cursor.execute(f"CREATE DATABASE {db_name};")
                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "database": db_name,
                    "message": f"PostgreSQL database {db_name} created"
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        elif db_type == "mysql":
            try:
                import mysql.connector

                conn = mysql.connector.connect(
                    host=db_config.get("host", "localhost"),
                    user=db_config.get("user", "root"),
                    password=db_config.get("password", "")
                )
                cursor = conn.cursor()

                db_name = db_config.get("database", "test_db")
                cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
                cursor.execute(f"CREATE DATABASE {db_name}")
                conn.commit()
                cursor.close()
                conn.close()

                return {
                    "success": True,
                    "database": db_name,
                    "message": f"MySQL database {db_name} created"
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        return {
            "success": False,
            "error": f"Unsupported database type: {db_type}"
        }

    @staticmethod
    def cleanup_test_database(db_config: Dict) -> Dict:
        """
        Cleanup test database.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Cleanup result
        """
        db_type = db_config.get("type", "sqlite")

        if db_type == "sqlite":
            db_path = db_config.get("path", "test.db")
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                return {
                    "success": True,
                    "message": f"SQLite database {db_path} deleted"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        elif db_type == "postgresql":
            try:
                import psycopg2

                conn = psycopg2.connect(
                    host=db_config.get("host", "localhost"),
                    user=db_config.get("user", "postgres"),
                    password=db_config.get("password", "")
                )
                cursor = conn.cursor()

                db_name = db_config.get("database", "test_db")
                cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "message": f"PostgreSQL database {db_name} dropped"
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        return {"success": True, "message": "No cleanup needed"}

    @staticmethod
    def run_migrations(migration_command: str) -> Dict:
        """
        Run database migrations.
        
        Args:
            migration_command: Migration command to run
            
        Returns:
            Migration result
        """
        try:
            result = subprocess.run(
                migration_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Migration command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_all_services()
        return False
