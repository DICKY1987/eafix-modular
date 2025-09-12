#!/usr/bin/env python3
"""
Predictive Failure Detection System
===================================

AI-powered system that analyzes patterns and predicts failures before they occur.
Uses machine learning, statistical analysis, and pattern recognition for proactive monitoring.
"""

import asyncio
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of failure predictions."""
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PERFORMANCE_DEGRADATION = "performance_degradation" 
    SERVICE_FAILURE = "service_failure"
    MEMORY_LEAK = "memory_leak"
    DISK_SPACE = "disk_space"
    NETWORK_ISSUES = "network_issues"
    ERROR_SPIKE = "error_spike"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MetricData:
    """System metric data point."""
    timestamp: datetime
    service_name: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    error_rate: float
    response_time: float
    active_connections: int
    request_rate: float


@dataclass
class PredictionResult:
    """Prediction result with details."""
    prediction_type: PredictionType
    severity: AlertSeverity
    confidence: float
    predicted_time: datetime
    affected_services: List[str]
    description: str
    recommended_actions: List[str]
    supporting_data: Dict[str, Any] = field(default_factory=dict)


class PredictiveFailureDetector:
    """Predicts system failures using machine learning and statistical analysis."""
    
    def __init__(self, data_dir: Path = Path("prediction_data")):
        """Initialize the predictive failure detector.
        
        Args:
            data_dir: Directory for storing models and data
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # Database for storing metrics
        self.db_path = self.data_dir / "metrics.db"
        self.init_database()
        
        # Models
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_dir = self.data_dir / "models"
        self.model_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.prediction_horizon = timedelta(hours=2)  # How far ahead to predict
        self.training_window = timedelta(days=7)  # Historical data for training
        self.min_data_points = 100  # Minimum data points for training
        
        # Thresholds
        self.anomaly_threshold = 0.1  # Anomaly detection threshold
        self.trend_threshold = 0.05  # Trend analysis threshold
        self.confidence_threshold = 0.7  # Minimum confidence for alerts
        
        # Active predictions
        self.active_predictions: List[PredictionResult] = []
        
        logger.info("PredictiveFailureDetector initialized")
    
    def init_database(self) -> None:
        """Initialize SQLite database for storing metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                service_name TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                network_io REAL,
                error_rate REAL,
                response_time REAL,
                active_connections INTEGER,
                request_rate REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON metrics(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_service_timestamp 
            ON metrics(service_name, timestamp)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized")
    
    def record_metrics(self, metrics: List[MetricData]) -> None:
        """Record system metrics for analysis.
        
        Args:
            metrics: List of metric data points to record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO metrics (
                    timestamp, service_name, cpu_usage, memory_usage, 
                    disk_usage, network_io, error_rate, response_time,
                    active_connections, request_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.timestamp,
                metric.service_name,
                metric.cpu_usage,
                metric.memory_usage,
                metric.disk_usage,
                metric.network_io,
                metric.error_rate,
                metric.response_time,
                metric.active_connections,
                metric.request_rate
            ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Recorded {len(metrics)} metric data points")
    
    def get_historical_data(self, service_name: Optional[str] = None, 
                          hours_back: int = 168) -> pd.DataFrame:
        """Get historical metric data.
        
        Args:
            service_name: Specific service name (None for all services)
            hours_back: Hours of historical data to retrieve
            
        Returns:
            DataFrame with historical metrics
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM metrics 
            WHERE timestamp > datetime('now', '-{} hours')
        '''.format(hours_back)
        
        if service_name:
            query += f" AND service_name = '{service_name}'"
        
        query += " ORDER BY timestamp ASC"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    async def train_models(self, force_retrain: bool = False) -> None:
        """Train predictive models using historical data.
        
        Args:
            force_retrain: Whether to force retraining even if models exist
        """
        logger.info("Starting model training...")
        
        # Get historical data
        df = self.get_historical_data()
        
        if df.empty or len(df) < self.min_data_points:
            logger.warning(f"Insufficient data for training ({len(df)} points)")
            return
        
        # Train models for each prediction type
        await self._train_resource_exhaustion_model(df)
        await self._train_performance_degradation_model(df)
        await self._train_service_failure_model(df)
        await self._train_anomaly_detection_model(df)
        
        # Save models
        self._save_models()
        
        logger.info("Model training completed")
    
    async def _train_resource_exhaustion_model(self, df: pd.DataFrame) -> None:
        """Train model to predict resource exhaustion."""
        logger.info("Training resource exhaustion model...")
        
        # Feature engineering
        features = []
        labels = []
        
        for service in df['service_name'].unique():
            service_data = df[df['service_name'] == service].copy()
            service_data = service_data.sort_values('timestamp')
            
            # Create sliding windows
            window_size = 10
            for i in range(len(service_data) - window_size):
                window = service_data.iloc[i:i+window_size]
                
                # Features: statistical measures over the window
                feature_vector = [
                    window['cpu_usage'].mean(),
                    window['cpu_usage'].std(),
                    window['cpu_usage'].max(),
                    window['memory_usage'].mean(),
                    window['memory_usage'].std(),
                    window['memory_usage'].max(),
                    window['disk_usage'].mean(),
                    window['disk_usage'].std(),
                    window['disk_usage'].max(),
                    # Trends
                    np.polyfit(range(len(window)), window['cpu_usage'], 1)[0],
                    np.polyfit(range(len(window)), window['memory_usage'], 1)[0],
                    np.polyfit(range(len(window)), window['disk_usage'], 1)[0],
                ]
                
                # Label: resource exhaustion in next period
                next_data = service_data.iloc[i+window_size:i+window_size+5]
                if not next_data.empty:
                    resource_exhausted = (
                        next_data['cpu_usage'].max() > 90 or
                        next_data['memory_usage'].max() > 90 or
                        next_data['disk_usage'].max() > 90
                    )
                    
                    features.append(feature_vector)
                    labels.append(1 if resource_exhausted else 0)
        
        if len(features) < 50:  # Minimum samples
            logger.warning("Insufficient data for resource exhaustion model")
            return
        
        X = np.array(features)
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        report = classification_report(y_test, y_pred, output_dict=True)
        logger.info(f"Resource exhaustion model accuracy: {report['accuracy']:.3f}")
        
        self.models['resource_exhaustion'] = model
        self.scalers['resource_exhaustion'] = scaler
    
    async def _train_performance_degradation_model(self, df: pd.DataFrame) -> None:
        """Train model to predict performance degradation."""
        logger.info("Training performance degradation model...")
        
        features = []
        labels = []
        
        for service in df['service_name'].unique():
            service_data = df[df['service_name'] == service].copy()
            service_data = service_data.sort_values('timestamp')
            
            if len(service_data) < 20:
                continue
            
            # Calculate rolling statistics
            service_data['response_time_ma'] = service_data['response_time'].rolling(5).mean()
            service_data['error_rate_ma'] = service_data['error_rate'].rolling(5).mean()
            
            window_size = 8
            for i in range(len(service_data) - window_size):
                window = service_data.iloc[i:i+window_size]
                
                if window['response_time_ma'].isna().any():
                    continue
                
                feature_vector = [
                    window['response_time'].mean(),
                    window['response_time'].std(),
                    window['response_time_ma'].iloc[-1],
                    window['error_rate'].mean(),
                    window['error_rate'].std(),
                    window['error_rate_ma'].iloc[-1],
                    window['cpu_usage'].mean(),
                    window['memory_usage'].mean(),
                    window['request_rate'].mean(),
                    window['active_connections'].mean(),
                    # Trends
                    np.polyfit(range(len(window)), window['response_time'], 1)[0],
                    np.polyfit(range(len(window)), window['error_rate'], 1)[0],
                ]
                
                # Label: performance degraded in next period
                next_data = service_data.iloc[i+window_size:i+window_size+3]
                if not next_data.empty:
                    baseline_response = window['response_time'].mean()
                    baseline_errors = window['error_rate'].mean()
                    
                    degraded = (
                        next_data['response_time'].mean() > baseline_response * 1.5 or
                        next_data['error_rate'].mean() > baseline_errors * 2
                    )
                    
                    features.append(feature_vector)
                    labels.append(1 if degraded else 0)
        
        if len(features) < 50:
            logger.warning("Insufficient data for performance degradation model")
            return
        
        X = np.array(features)
        y = np.array(labels)
        
        # Handle class imbalance
        from collections import Counter
        counter = Counter(y)
        if counter[1] < 5:  # Too few positive examples
            logger.warning("Too few performance degradation examples")
            return
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        report = classification_report(y_test, y_pred, output_dict=True)
        logger.info(f"Performance degradation model accuracy: {report['accuracy']:.3f}")
        
        self.models['performance_degradation'] = model
        self.scalers['performance_degradation'] = scaler
    
    async def _train_service_failure_model(self, df: pd.DataFrame) -> None:
        """Train model to predict service failures."""
        logger.info("Training service failure model...")
        
        # This would be enhanced with actual failure data
        # For now, we'll use proxy indicators
        features = []
        labels = []
        
        for service in df['service_name'].unique():
            service_data = df[df['service_name'] == service].copy()
            service_data = service_data.sort_values('timestamp')
            
            window_size = 6
            for i in range(len(service_data) - window_size):
                window = service_data.iloc[i:i+window_size]
                
                feature_vector = [
                    window['error_rate'].mean(),
                    window['error_rate'].max(),
                    window['error_rate'].std(),
                    window['response_time'].mean(),
                    window['response_time'].max(),
                    window['cpu_usage'].std(),  # High variability can indicate instability
                    window['memory_usage'].std(),
                    window['active_connections'].std(),
                    # Recent spike indicators
                    1 if window['error_rate'].max() > window['error_rate'].mean() * 3 else 0,
                    1 if window['response_time'].max() > window['response_time'].mean() * 5 else 0,
                ]
                
                # Label: high probability of failure (proxy)
                next_data = service_data.iloc[i+window_size:i+window_size+2]
                if not next_data.empty:
                    failure_indicators = (
                        next_data['error_rate'].max() > 0.1 or  # 10% error rate
                        next_data['response_time'].max() > 10.0 or  # Very slow response
                        next_data['cpu_usage'].max() > 95  # CPU spike
                    )
                    
                    features.append(feature_vector)
                    labels.append(1 if failure_indicators else 0)
        
        if len(features) < 50:
            logger.warning("Insufficient data for service failure model")
            return
        
        X = np.array(features)
        y = np.array(labels)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        report = classification_report(y_test, y_pred, output_dict=True)
        logger.info(f"Service failure model accuracy: {report['accuracy']:.3f}")
        
        self.models['service_failure'] = model
        self.scalers['service_failure'] = scaler
    
    async def _train_anomaly_detection_model(self, df: pd.DataFrame) -> None:
        """Train anomaly detection model."""
        logger.info("Training anomaly detection model...")
        
        # Use all numerical features for anomaly detection
        feature_columns = [
            'cpu_usage', 'memory_usage', 'disk_usage', 'network_io',
            'error_rate', 'response_time', 'active_connections', 'request_rate'
        ]
        
        X = df[feature_columns].dropna()
        
        if len(X) < 100:
            logger.warning("Insufficient data for anomaly detection")
            return
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train isolation forest
        model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42
        )
        model.fit(X_scaled)
        
        self.models['anomaly_detection'] = model
        self.scalers['anomaly_detection'] = scaler
        
        logger.info("Anomaly detection model trained")
    
    async def predict_failures(self) -> List[PredictionResult]:
        """Generate failure predictions based on current data.
        
        Returns:
            List of prediction results
        """
        predictions = []
        
        # Get recent data for prediction
        recent_df = self.get_historical_data(hours_back=6)
        
        if recent_df.empty:
            logger.warning("No recent data for predictions")
            return predictions
        
        # Load models if not in memory
        self._load_models()
        
        # Generate predictions for each service
        for service_name in recent_df['service_name'].unique():
            service_predictions = await self._predict_for_service(service_name, recent_df)
            predictions.extend(service_predictions)
        
        # Filter by confidence threshold
        high_confidence_predictions = [
            p for p in predictions 
            if p.confidence >= self.confidence_threshold
        ]
        
        self.active_predictions = high_confidence_predictions
        
        logger.info(f"Generated {len(high_confidence_predictions)} high-confidence predictions")
        
        return high_confidence_predictions
    
    async def _predict_for_service(self, service_name: str, df: pd.DataFrame) -> List[PredictionResult]:
        """Generate predictions for a specific service.
        
        Args:
            service_name: Name of the service
            df: Historical data DataFrame
            
        Returns:
            List of predictions for this service
        """
        predictions = []
        service_data = df[df['service_name'] == service_name].copy()
        
        if len(service_data) < 10:
            return predictions
        
        service_data = service_data.sort_values('timestamp')
        
        # Resource exhaustion prediction
        if 'resource_exhaustion' in self.models:
            pred = await self._predict_resource_exhaustion(service_name, service_data)
            if pred:
                predictions.append(pred)
        
        # Performance degradation prediction
        if 'performance_degradation' in self.models:
            pred = await self._predict_performance_degradation(service_name, service_data)
            if pred:
                predictions.append(pred)
        
        # Service failure prediction
        if 'service_failure' in self.models:
            pred = await self._predict_service_failure(service_name, service_data)
            if pred:
                predictions.append(pred)
        
        # Anomaly detection
        if 'anomaly_detection' in self.models:
            pred = await self._predict_anomalies(service_name, service_data)
            if pred:
                predictions.extend(pred)
        
        return predictions
    
    async def _predict_resource_exhaustion(self, service_name: str, 
                                         data: pd.DataFrame) -> Optional[PredictionResult]:
        """Predict resource exhaustion for a service."""
        model = self.models['resource_exhaustion']
        scaler = self.scalers['resource_exhaustion']
        
        # Prepare features from recent data
        window_size = 10
        if len(data) < window_size:
            return None
        
        window = data.tail(window_size)
        
        try:
            feature_vector = [
                window['cpu_usage'].mean(),
                window['cpu_usage'].std(),
                window['cpu_usage'].max(),
                window['memory_usage'].mean(),
                window['memory_usage'].std(),
                window['memory_usage'].max(),
                window['disk_usage'].mean(),
                window['disk_usage'].std(),
                window['disk_usage'].max(),
                np.polyfit(range(len(window)), window['cpu_usage'], 1)[0],
                np.polyfit(range(len(window)), window['memory_usage'], 1)[0],
                np.polyfit(range(len(window)), window['disk_usage'], 1)[0],
            ]
            
            X = scaler.transform([feature_vector])
            probability = model.predict_proba(X)[0][1]  # Probability of failure
            
            if probability > self.confidence_threshold:
                # Determine which resource will be exhausted
                cpu_trend = feature_vector[9]
                memory_trend = feature_vector[10]
                disk_trend = feature_vector[11]
                
                resource_type = "CPU"
                if memory_trend > cpu_trend and memory_trend > disk_trend:
                    resource_type = "Memory"
                elif disk_trend > cpu_trend and disk_trend > memory_trend:
                    resource_type = "Disk"
                
                # Estimate time to exhaustion based on trend
                current_usage = window[f'{resource_type.lower()}_usage'].iloc[-1]
                trend_rate = locals()[f'{resource_type.lower()}_trend']
                
                if trend_rate > 0:
                    hours_to_exhaustion = (95 - current_usage) / trend_rate
                    predicted_time = datetime.now() + timedelta(hours=hours_to_exhaustion)
                else:
                    predicted_time = datetime.now() + self.prediction_horizon
                
                return PredictionResult(
                    prediction_type=PredictionType.RESOURCE_EXHAUSTION,
                    severity=AlertSeverity.CRITICAL if probability > 0.8 else AlertSeverity.WARNING,
                    confidence=probability,
                    predicted_time=predicted_time,
                    affected_services=[service_name],
                    description=f"{resource_type} exhaustion predicted for {service_name}",
                    recommended_actions=[
                        f"Scale {resource_type.lower()} resources for {service_name}",
                        f"Check for {resource_type.lower()} leaks or inefficiencies",
                        "Consider load balancing or traffic reduction",
                        "Monitor resource usage closely"
                    ],
                    supporting_data={
                        'current_cpu': current_usage if resource_type == 'CPU' else window['cpu_usage'].iloc[-1],
                        'current_memory': current_usage if resource_type == 'Memory' else window['memory_usage'].iloc[-1],
                        'current_disk': current_usage if resource_type == 'Disk' else window['disk_usage'].iloc[-1],
                        'trend_rate': trend_rate,
                        'critical_resource': resource_type
                    }
                )
        
        except Exception as e:
            logger.warning(f"Error predicting resource exhaustion for {service_name}: {e}")
        
        return None
    
    async def _predict_performance_degradation(self, service_name: str, 
                                             data: pd.DataFrame) -> Optional[PredictionResult]:
        """Predict performance degradation for a service."""
        model = self.models['performance_degradation']
        scaler = self.scalers['performance_degradation']
        
        window_size = 8
        if len(data) < window_size:
            return None
        
        window = data.tail(window_size)
        
        try:
            # Calculate moving averages
            response_time_ma = window['response_time'].rolling(5).mean().iloc[-1]
            error_rate_ma = window['error_rate'].rolling(5).mean().iloc[-1]
            
            feature_vector = [
                window['response_time'].mean(),
                window['response_time'].std(),
                response_time_ma,
                window['error_rate'].mean(),
                window['error_rate'].std(),
                error_rate_ma,
                window['cpu_usage'].mean(),
                window['memory_usage'].mean(),
                window['request_rate'].mean(),
                window['active_connections'].mean(),
                np.polyfit(range(len(window)), window['response_time'], 1)[0],
                np.polyfit(range(len(window)), window['error_rate'], 1)[0],
            ]
            
            X = scaler.transform([feature_vector])
            probability = model.predict_proba(X)[0][1]
            
            if probability > self.confidence_threshold:
                return PredictionResult(
                    prediction_type=PredictionType.PERFORMANCE_DEGRADATION,
                    severity=AlertSeverity.WARNING if probability < 0.8 else AlertSeverity.CRITICAL,
                    confidence=probability,
                    predicted_time=datetime.now() + timedelta(minutes=30),
                    affected_services=[service_name],
                    description=f"Performance degradation predicted for {service_name}",
                    recommended_actions=[
                        "Check application performance metrics",
                        "Review recent deployments or configuration changes",
                        "Monitor database queries and external API calls",
                        "Consider scaling resources or optimizing code",
                        "Check for memory leaks or resource contention"
                    ],
                    supporting_data={
                        'current_response_time': window['response_time'].iloc[-1],
                        'current_error_rate': window['error_rate'].iloc[-1],
                        'response_time_trend': feature_vector[10],
                        'error_rate_trend': feature_vector[11]
                    }
                )
        
        except Exception as e:
            logger.warning(f"Error predicting performance degradation for {service_name}: {e}")
        
        return None
    
    async def _predict_service_failure(self, service_name: str, 
                                     data: pd.DataFrame) -> Optional[PredictionResult]:
        """Predict service failure."""
        model = self.models['service_failure']
        scaler = self.scalers['service_failure']
        
        window_size = 6
        if len(data) < window_size:
            return None
        
        window = data.tail(window_size)
        
        try:
            feature_vector = [
                window['error_rate'].mean(),
                window['error_rate'].max(),
                window['error_rate'].std(),
                window['response_time'].mean(),
                window['response_time'].max(),
                window['cpu_usage'].std(),
                window['memory_usage'].std(),
                window['active_connections'].std(),
                1 if window['error_rate'].max() > window['error_rate'].mean() * 3 else 0,
                1 if window['response_time'].max() > window['response_time'].mean() * 5 else 0,
            ]
            
            X = scaler.transform([feature_vector])
            probability = model.predict_proba(X)[0][1]
            
            if probability > self.confidence_threshold:
                return PredictionResult(
                    prediction_type=PredictionType.SERVICE_FAILURE,
                    severity=AlertSeverity.CRITICAL,
                    confidence=probability,
                    predicted_time=datetime.now() + timedelta(minutes=15),
                    affected_services=[service_name],
                    description=f"Service failure predicted for {service_name}",
                    recommended_actions=[
                        "Prepare for immediate service restart",
                        "Check service health and dependencies",
                        "Review error logs and system resources",
                        "Consider enabling circuit breaker",
                        "Notify operations team",
                        "Prepare rollback plan if recent deployment"
                    ],
                    supporting_data={
                        'error_spike_detected': feature_vector[8] == 1,
                        'response_spike_detected': feature_vector[9] == 1,
                        'max_error_rate': window['error_rate'].max(),
                        'max_response_time': window['response_time'].max()
                    }
                )
        
        except Exception as e:
            logger.warning(f"Error predicting service failure for {service_name}: {e}")
        
        return None
    
    async def _predict_anomalies(self, service_name: str, 
                               data: pd.DataFrame) -> List[PredictionResult]:
        """Predict anomalies using isolation forest."""
        model = self.models['anomaly_detection']
        scaler = self.scalers['anomaly_detection']
        
        predictions = []
        
        feature_columns = [
            'cpu_usage', 'memory_usage', 'disk_usage', 'network_io',
            'error_rate', 'response_time', 'active_connections', 'request_rate'
        ]
        
        # Check recent data points for anomalies
        recent_data = data.tail(5)[feature_columns].dropna()
        
        if recent_data.empty:
            return predictions
        
        try:
            X_scaled = scaler.transform(recent_data)
            anomaly_scores = model.decision_function(X_scaled)
            is_anomaly = model.predict(X_scaled)
            
            # Find significant anomalies
            for i, (score, is_anom) in enumerate(zip(anomaly_scores, is_anomaly)):
                if is_anom == -1 and score < -0.1:  # Strong anomaly
                    confidence = min(abs(score), 1.0)
                    
                    predictions.append(PredictionResult(
                        prediction_type=PredictionType.ERROR_SPIKE,
                        severity=AlertSeverity.WARNING,
                        confidence=confidence,
                        predicted_time=datetime.now(),
                        affected_services=[service_name],
                        description=f"Anomalous behavior detected in {service_name}",
                        recommended_actions=[
                            "Investigate unusual system behavior",
                            "Check for configuration changes",
                            "Review system logs for errors",
                            "Monitor service closely for additional anomalies"
                        ],
                        supporting_data={
                            'anomaly_score': float(score),
                            'data_point': recent_data.iloc[i].to_dict()
                        }
                    ))
        
        except Exception as e:
            logger.warning(f"Error detecting anomalies for {service_name}: {e}")
        
        return predictions
    
    def _save_models(self) -> None:
        """Save trained models to disk."""
        try:
            for name, model in self.models.items():
                model_path = self.model_dir / f"{name}_model.joblib"
                joblib.dump(model, model_path)
                
                if name in self.scalers:
                    scaler_path = self.model_dir / f"{name}_scaler.joblib"
                    joblib.dump(self.scalers[name], scaler_path)
            
            logger.info("Models saved successfully")
        
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self) -> None:
        """Load trained models from disk."""
        try:
            for model_file in self.model_dir.glob("*_model.joblib"):
                name = model_file.stem.replace("_model", "")
                self.models[name] = joblib.load(model_file)
                
                scaler_file = self.model_dir / f"{name}_scaler.joblib"
                if scaler_file.exists():
                    self.scalers[name] = joblib.load(scaler_file)
            
            logger.info(f"Loaded {len(self.models)} models")
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """Get summary of active predictions.
        
        Returns:
            Summary of predictions by type and severity
        """
        summary = {
            'total_predictions': len(self.active_predictions),
            'by_type': {},
            'by_severity': {},
            'critical_services': []
        }
        
        for pred in self.active_predictions:
            # Count by type
            pred_type = pred.prediction_type.value
            summary['by_type'][pred_type] = summary['by_type'].get(pred_type, 0) + 1
            
            # Count by severity
            severity = pred.severity.value
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Track critical services
            if pred.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                summary['critical_services'].extend(pred.affected_services)
        
        summary['critical_services'] = list(set(summary['critical_services']))
        
        return summary


# Example usage
async def main():
    """Example usage of the PredictiveFailureDetector."""
    detector = PredictiveFailureDetector()
    
    # Simulate some metric data
    import random
    current_time = datetime.now()
    
    metrics = []
    for i in range(100):
        timestamp = current_time - timedelta(hours=i/10)
        
        # Simulate degrading performance over time
        base_cpu = 50 + i * 0.3 + random.uniform(-10, 10)
        base_memory = 60 + i * 0.2 + random.uniform(-5, 5)
        
        metric = MetricData(
            timestamp=timestamp,
            service_name="api_server",
            cpu_usage=max(0, min(100, base_cpu)),
            memory_usage=max(0, min(100, base_memory)),
            disk_usage=70 + random.uniform(-5, 5),
            network_io=random.uniform(100, 1000),
            error_rate=0.01 + i * 0.001,
            response_time=0.1 + i * 0.01,
            active_connections=random.randint(50, 200),
            request_rate=random.uniform(100, 500)
        )
        metrics.append(metric)
    
    # Record metrics
    detector.record_metrics(metrics)
    
    # Train models
    await detector.train_models()
    
    # Generate predictions
    predictions = await detector.predict_failures()
    
    print(f"Generated {len(predictions)} predictions:")
    for pred in predictions:
        print(f"- {pred.prediction_type.value}: {pred.description} (confidence: {pred.confidence:.2f})")
        for action in pred.recommended_actions:
            print(f"  * {action}")
    
    # Get summary
    summary = detector.get_prediction_summary()
    print(f"\nPrediction Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())