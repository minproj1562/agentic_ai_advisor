# academic-advisor-backend/app/scripts/view_training_data.py
"""
View and export training dataset
Run: python -m scripts.view_training_data
"""

import sys
import os
import json
import csv
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.utils.training import generate_training_dataset, STUDENT_ARCHETYPES


def view_archetypes():
    """View the student archetype definitions"""
    print("\n" + "=" * 70)
    print("STUDENT ARCHETYPES (Template Definitions)")
    print("=" * 70)
    
    for label, archetype in STUDENT_ARCHETYPES.items():
        print(f"\n{'─' * 50}")
        print(f"📚 {label} - {archetype['description']}")
        print(f"{'─' * 50}")
        
        print("\n  STRONG SUBJECTS:")
        for subj, (low, high) in archetype['strong_subjects'].items():
            print(f"    • {subj}: {low}-{high} marks")
        
        print("\n  WEAK SUBJECTS:")
        for subj, (low, high) in archetype['weak_subjects'].items():
            print(f"    • {subj}: {low}-{high} marks")
        
        print("\n  INTERESTS:")
        for interest in archetype['interests']:
            print(f"    • {interest}")
        
        print("\n  PROJECT KEYWORDS:")
        print(f"    {', '.join(archetype['project_keywords'][:8])}...")
        
        print("\n  LANGUAGES & FRAMEWORKS:")
        print(f"    Languages: {', '.join(archetype['languages'])}")
        print(f"    Frameworks: {', '.join(archetype['frameworks'])}")


def view_sample_data(n_samples: int = 5):
    """Generate and view sample training data"""
    print("\n" + "=" * 70)
    print(f"SAMPLE TRAINING DATA ({n_samples} samples per class)")
    print("=" * 70)
    
    # Generate small dataset for viewing
    dataset = generate_training_dataset(n_samples_per_class=n_samples)
    
    # Group by label
    by_label = {}
    for sample in dataset:
        label = sample['label']
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(sample)
    
    for label, samples in by_label.items():
        print(f"\n{'─' * 50}")
        print(f"📊 Label: {label} ({len(samples)} samples)")
        print(f"{'─' * 50}")
        
        # Show first 2 samples in detail
        for i, sample in enumerate(samples[:2]):
            print(f"\n  Sample {i+1}:")
            print(f"    Source: {sample.get('source', 'synthetic')}")
            
            # Show marks (top 5 by value)
            marks = sample.get('marks', {})
            sorted_marks = sorted(marks.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"    Top Marks:")
            for subj, mark in sorted_marks:
                print(f"      • {subj}: {mark}")
            
            # Show interests
            interests = sample.get('interests', [])
            print(f"    Interests: {interests}")
            
            # Show projects summary
            projects = sample.get('projects', [])
            print(f"    Projects: {len(projects)}")
            if projects:
                print(f"      • {projects[0].get('title', 'Untitled')}")
                skills = projects[0].get('extracted_skills', [])[:5]
                print(f"        Skills: {', '.join(skills)}")
    
    return dataset


def export_to_json(n_samples: int = 10, filename: str = "training_data_sample.json"):
    """Export training data to JSON file"""
    dataset = generate_training_dataset(n_samples_per_class=n_samples)
    
    output_path = os.path.join(os.path.dirname(__file__), filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Exported {len(dataset)} samples to: {output_path}")
    return output_path


def export_to_csv(n_samples: int = 10, filename: str = "training_data_sample.csv"):
    """Export training data to CSV (flattened format)"""
    dataset = generate_training_dataset(n_samples_per_class=n_samples)
    
    output_path = os.path.join(os.path.dirname(__file__), filename)
    
    # Flatten the data for CSV
    rows = []
    for sample in dataset:
        row = {
            'label': sample['label'],
            'source': sample.get('source', 'synthetic'),
            'num_subjects': len(sample.get('marks', {})),
            'num_interests': len(sample.get('interests', [])),
            'num_projects': len(sample.get('projects', [])),
            'interests': '|'.join(sample.get('interests', [])),
        }
        
        # Add top 5 marks
        marks = sample.get('marks', {})
        sorted_marks = sorted(marks.items(), key=lambda x: x[1], reverse=True)
        for i, (subj, mark) in enumerate(sorted_marks[:5]):
            row[f'subject_{i+1}'] = subj
            row[f'mark_{i+1}'] = mark
        
        # Add project info
        projects = sample.get('projects', [])
        if projects:
            row['project_1_title'] = projects[0].get('title', '')
            row['project_1_skills'] = '|'.join(projects[0].get('extracted_skills', [])[:5])
        
        rows.append(row)
    
    # Write CSV
    if rows:
        fieldnames = rows[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"\n✅ Exported {len(rows)} samples to: {output_path}")
    return output_path


def view_statistics(n_samples: int = 50):
    """View statistics about the generated dataset"""
    print("\n" + "=" * 70)
    print("DATASET STATISTICS")
    print("=" * 70)
    
    dataset = generate_training_dataset(n_samples_per_class=n_samples)
    
    # Count by label
    label_counts = {}
    for sample in dataset:
        label = sample['label']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print(f"\nTotal samples: {len(dataset)}")
    print("\nSamples per class:")
    for label, count in sorted(label_counts.items()):
        print(f"  • {label}: {count} ({count/len(dataset)*100:.1f}%)")
    
    # Average marks per class
    print("\nAverage marks per class:")
    for label in ['ML', 'WT', 'DWM', 'CCS']:
        samples = [s for s in dataset if s['label'] == label]
        all_marks = []
        for s in samples:
            all_marks.extend(s.get('marks', {}).values())
        if all_marks:
            avg = sum(all_marks) / len(all_marks)
            print(f"  • {label}: {avg:.1f}")
    
    # Average projects per class
    print("\nAverage projects per class:")
    for label in ['ML', 'WT', 'DWM', 'CCS']:
        samples = [s for s in dataset if s['label'] == label]
        avg_projects = sum(len(s.get('projects', [])) for s in samples) / len(samples)
        print(f"  • {label}: {avg_projects:.1f}")
    
    # Interest distribution
    print("\nInterest distribution (across all samples):")
    interest_counts = {}
    for sample in dataset:
        for interest in sample.get('interests', []):
            interest_counts[interest] = interest_counts.get(interest, 0) + 1
    
    for interest, count in sorted(interest_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {interest}: {count}")


def main():
    """Main function to view training data"""
    print("\n" + "🎓" * 35)
    print("  ACADEMIC ADVISOR - TRAINING DATA VIEWER")
    print("🎓" * 35)
    
    while True:
        print("\n" + "─" * 50)
        print("OPTIONS:")
        print("  1. View Student Archetypes (templates)")
        print("  2. View Sample Training Data")
        print("  3. View Dataset Statistics")
        print("  4. Export to JSON")
        print("  5. Export to CSV")
        print("  6. View Single Sample (detailed)")
        print("  0. Exit")
        print("─" * 50)
        
        choice = input("\nEnter choice (0-6): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        elif choice == '1':
            view_archetypes()
        elif choice == '2':
            n = input("Samples per class (default 3): ").strip()
            n = int(n) if n.isdigit() else 3
            view_sample_data(n)
        elif choice == '3':
            n = input("Samples per class for stats (default 50): ").strip()
            n = int(n) if n.isdigit() else 50
            view_statistics(n)
        elif choice == '4':
            n = input("Samples per class (default 25): ").strip()
            n = int(n) if n.isdigit() else 25
            export_to_json(n)
        elif choice == '5':
            n = input("Samples per class (default 25): ").strip()
            n = int(n) if n.isdigit() else 25
            export_to_csv(n)
        elif choice == '6':
            from app.ml.utils.training import generate_synthetic_sample
            label = input("Label (ML/WT/DWM/CCS, default ML): ").strip().upper()
            if label not in ['ML', 'WT', 'DWM', 'CCS']:
                label = 'ML'
            sample = generate_synthetic_sample(label)
            print(f"\n{'─' * 50}")
            print(f"DETAILED SAMPLE - {label}")
            print(f"{'─' * 50}")
            print(json.dumps(sample, indent=2))
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()