#!/usr/bin/env python3
"""
Machine Learning Pipeline for SDN Conflict Flow Detection
Implements: DT, SVM, EFDT, and Hybrid DT-SVM algorithms
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.preprocessing import LabelEncoder
import time
import json
import sys

class SDNConflictDetector:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.label_encoder = LabelEncoder()
        self.results = {}
    
    def load_and_preprocess(self):
        """Load CSV and preprocess features"""
        print(f"Loading data from {self.csv_file}...")
        self.df = pd.read_csv(self.csv_file)
        
        print(f"Total flows: {len(self.df)}")
        print(f"Normal flows: {len(self.df[self.df['flow_type'] == 'normal'])}")
        print(f"Conflict flows: {len(self.df[self.df['flow_type'] == 'conflict'])}")
        
        # Feature engineering
        self.df['priority_normalized'] = self.df['priority'] / 500
        self.df['action_code'] = self.df['action'].apply(self._encode_action)
        self.df['ipv4_src_numeric'] = self.df['ipv4_src'].apply(self._ip_to_numeric)
        self.df['ipv4_dst_numeric'] = self.df['ipv4_dst'].apply(self._ip_to_numeric)
        
        # Binary classification: normal (0) vs conflict (1)
        self.df['is_conflict'] = (self.df['flow_type'] == 'conflict').astype(int)
        
        print("Data preprocessing complete.")
    
    def _ip_to_numeric(self, ip_str):
        """Convert IP address to numeric value"""
        if ip_str == 'any' or pd.isna(ip_str):
            return 0
        try:
            parts = str(ip_str).split('.')
            if len(parts) == 4:
                return sum(int(p) << (8 * (3 - i)) for i, p in enumerate(parts))
        except:
            pass
        return 0
    
    def _encode_action(self, action_str):
        """Encode action to numeric"""
        if pd.isna(action_str):
            return 0
        action_str = str(action_str)
        if 'OUTPUT:1' in action_str:
            return 1
        elif 'OUTPUT:2' in action_str:
            return 2
        elif 'OUTPUT:3' in action_str:
            return 3
        elif 'DROP' in action_str or action_str == '':
            return 0
        return len(action_str.split(','))  # Count number of outputs
    
    def prepare_features(self):
        """Prepare feature matrix for training"""
        features = [
            'dpid', 'priority_normalized', 'in_port', 
            'eth_type', 'action_code', 'ipv4_src_numeric', 'ipv4_dst_numeric'
        ]
        
        X = self.df[features].fillna(0)
        y = self.df['is_conflict']
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(self.X_train)} samples")
        print(f"Test set: {len(self.X_test)} samples")
    
    def train_decision_tree(self):
        """Train Decision Tree classifier"""
        print("\n" + "="*50)
        print("Training DECISION TREE (DT)")
        print("="*50)
        
        start_time = time.time()
        
        model = DecisionTreeClassifier(
            criterion='gini',
            max_depth=None,
            min_samples_split=2,
            random_state=42
        )
        
        model.fit(self.X_train, self.y_train)
        y_pred = model.predict(self.X_test)
        
        elapsed_time = time.time() - start_time
        
        results = self._calculate_metrics(self.y_test, y_pred, elapsed_time)
        self.results['DT'] = results
        self._print_results('Decision Tree', results)
        
        return model
    
    def train_svm(self):
        """Train Support Vector Machine classifier"""
        print("\n" + "="*50)
        print("Training SUPPORT VECTOR MACHINE (SVM)")
        print("="*50)
        
        start_time = time.time()
        
        model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            random_state=42
        )
        
        model.fit(self.X_train, self.y_train)
        y_pred = model.predict(self.X_test)
        
        elapsed_time = time.time() - start_time
        
        results = self._calculate_metrics(self.y_test, y_pred, elapsed_time)
        self.results['SVM'] = results
        self._print_results('SVM', results)
        
        return model
    
    def train_efdt(self):
        """Train Extremely Fast Decision Tree (simulated with optimized DT)"""
        print("\n" + "="*50)
        print("Training EXTREMELY FAST DECISION TREE (EFDT)")
        print("="*50)
        
        start_time = time.time()
        
        # EFDT simulation using optimized decision tree
        # In production, use skmultiflow's HoeffdingTreeClassifier
        model = DecisionTreeClassifier(
            criterion='gini',
            max_depth=10,  # Limited depth for speed
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        model.fit(self.X_train, self.y_train)
        y_pred = model.predict(self.X_test)
        
        elapsed_time = time.time() - start_time
        
        results = self._calculate_metrics(self.y_test, y_pred, elapsed_time)
        self.results['EFDT'] = results
        self._print_results('EFDT', results)
        
        return model
    
    def train_hybrid_dt_svm(self):
        """Train Hybrid DT-SVM using ensemble voting"""
        print("\n" + "="*50)
        print("Training HYBRID DT-SVM")
        print("="*50)
        
        start_time = time.time()
        
        dt = DecisionTreeClassifier(random_state=42)
        svm = SVC(kernel='rbf', probability=True, random_state=42)
        
        model = VotingClassifier(
            estimators=[('dt', dt), ('svm', svm)],
            voting='hard'
        )
        
        model.fit(self.X_train, self.y_train)
        y_pred = model.predict(self.X_test)
        
        elapsed_time = time.time() - start_time
        
        results = self._calculate_metrics(self.y_test, y_pred, elapsed_time)
        self.results['Hybrid_DT_SVM'] = results
        self._print_results('Hybrid DT-SVM', results)
        
        return model
    
    def _calculate_metrics(self, y_true, y_pred, elapsed_time):
        """Calculate all evaluation metrics"""
        return {
            'accuracy': accuracy_score(y_true, y_pred) * 100,
            'precision': precision_score(y_true, y_pred, average='binary', zero_division=0) * 100,
            'recall': recall_score(y_true, y_pred, average='binary', zero_division=0) * 100,
            'f1_score': f1_score(y_true, y_pred, average='binary', zero_division=0) * 100,
            'execution_time': elapsed_time
        }
    
    def _print_results(self, name, results):
        """Print formatted results"""
        print(f"\n{name} Results:")
        print(f"  Accuracy:   {results['accuracy']:.2f}%")
        print(f"  Precision:  {results['precision']:.2f}%")
        print(f"  Recall:     {results['recall']:.2f}%")
        print(f"  F1-Score:   {results['f1_score']:.2f}%")
        print(f"  Time:       {results['execution_time']:.6f} seconds")
    
    def classify_conflict_types(self):
        """Phase 2: Classify conflict types (7-class classification)"""
        print("\n" + "="*50)
        print("PHASE 2: CONFLICT TYPE CLASSIFICATION")
        print("="*50)
        
        # Filter only conflict flows
        conflict_df = self.df[self.df['flow_type'] == 'conflict'].copy()
        
        if len(conflict_df) == 0:
            print("No conflict flows to classify!")
            return None
        
        # Prepare features
        features = [
            'dpid', 'priority_normalized', 'in_port',
            'eth_type', 'action_code', 'ipv4_src_numeric', 'ipv4_dst_numeric'
        ]
        
        X = conflict_df[features].fillna(0)
        y = conflict_df['conflict_type']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
        
        print(f"Training on {len(X_train)} conflict flows")
        print(f"Testing on {len(X_test)} conflict flows")
        
        start_time = time.time()
        
        # Use EFDT for classification (best performer from paper)
        model = DecisionTreeClassifier(
            criterion='gini',
            max_depth=15,
            min_samples_split=3,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        elapsed_time = time.time() - start_time
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred) * 100
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0) * 100
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0) * 100
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0) * 100
        
        print(f"\nConflict Type Classification Results:")
        print(f"  Accuracy:   {accuracy:.2f}%")
        print(f"  Precision:  {precision:.2f}%")
        print(f"  Recall:     {recall:.2f}%")
        print(f"  F1-Score:   {f1:.2f}%")
        print(f"  Time:       {elapsed_time:.6f} seconds")
        
        print("\nDetailed Classification Report:")
        print(classification_report(y_test, y_pred))
        
        self.results['classification'] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'execution_time': elapsed_time
        }
        
        return model
    
    def compare_algorithms(self):
        """Print comparison table of all algorithms"""
        print("\n" + "="*60)
        print("ALGORITHM COMPARISON SUMMARY")
        print("="*60)
        
        if not self.results:
            print("No results to compare. Run training first.")
            return
        
        print(f"{'Algorithm':<20} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Time (s)':<12}")
        print("-" * 80)
        
        for alg_name, metrics in self.results.items():
            if alg_name != 'classification':
                print(f"{alg_name:<20} {metrics['accuracy']:>10.2f}% {metrics['precision']:>10.2f}% "
                      f"{metrics['recall']:>10.2f}% {metrics['f1_score']:>10.2f}% {metrics['execution_time']:>10.6f}")
        
        # Find best algorithm
        best_alg = max(
            [(k, v) for k, v in self.results.items() if k != 'classification'],
            key=lambda x: x[1]['accuracy']
        )
        print(f"\n🏆 Best Algorithm: {best_alg[0]} with {best_alg[1]['accuracy']:.2f}% accuracy")
    
    def save_results(self, filename='ml_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {filename}")
    
    def run_full_pipeline(self):
        """Run complete ML pipeline"""
        print("="*60)
        print("SDN CONFLICT DETECTION - ML PIPELINE")
        print("="*60)
        
        # Step 1: Load and preprocess
        self.load_and_preprocess()
        
        # Step 2: Prepare features
        self.prepare_features()
        
        # Step 3: Train all detection models
        print("\n--- PHASE 1: CONFLICT DETECTION (Binary Classification) ---")
        self.train_decision_tree()
        self.train_svm()
        self.train_efdt()
        self.train_hybrid_dt_svm()
        
        # Step 4: Conflict type classification
        self.classify_conflict_types()
        
        # Step 5: Compare results
        self.compare_algorithms()
        
        # Step 6: Save results
        self.save_results()
        
        return self.results


def main():
    if len(sys.argv) < 2:
        print("Usage: python ml_detector.py <csv_file>")
        print("Example: python ml_detector.py flows_1357_20251115_125845.csv")
        return
    
    csv_file = sys.argv[1]
    
    detector = SDNConflictDetector(csv_file)
    results = detector.run_full_pipeline()
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
