"""
Comprehensive demonstration of EGIF transformations on corpus examples.
Shows how to parse corpus EGIFs, apply various transformation rules, and generate new EGIFs.
"""

import json
from pathlib import Path

from egif_transformation_interface import (
    EGIFTransformationInterface,
    TransformationRequest,
)


def demonstrate_multiple_transformations():
    """Demonstrate various transformations on different corpus EGIFs."""

    interface = EGIFTransformationInterface()

    print("🎭 Comprehensive EGIF Transformation Demonstrations")
    print("=" * 60)

    # Example 1: INS - Insert Teacher relation into Socrates example
    print("\n📚 Example 1: Insertion (INS) - Adding Teacher relation")
    print("-" * 50)

    socrates_path = "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.json"

    result1 = interface.demonstrate_transformation(
        corpus_path=socrates_path,
        rule_name="INS",
        target_area_description="second_negation",
        operation_details={"insert_content": '(Teacher "Socrates")'},
        description='Insert (Teacher "Socrates") in the inner negation',
    )

    if result1.success:
        print(f"✅ Successfully transformed:")
        print(f"   From: {result1.original_egif}")
        print(f"   To:   {result1.result_egif}")
        print(f"   Interpretation: If human Socrates, then mortal AND teacher Socrates")

    # Example 2: DC+ - Add double cut around existing content
    print("\n🔄 Example 2: Double Cut Insertion (DC+)")
    print("-" * 50)

    # Use the result from example 1 as input for DC+
    if result1.success:
        result2 = interface.apply_transformation(
            TransformationRequest(
                source_egif=result1.result_egif,
                rule_name="DC+",
                target_area_description="sheet",
                operation_details={"selected_elements": []},  # Empty double cut
                description="Add empty double cut on sheet",
            )
        )

        if result2.success:
            print(f"✅ Successfully added double cut:")
            print(f"   From: {result2.original_egif}")
            print(f"   To:   {result2.result_egif}")
            print(f"   Interpretation: Added logical structure for further operations")

    # Example 3: ERA - Erase an element from positive area
    print("\n🗑️  Example 3: Erasure (ERA) - Remove element")
    print("-" * 50)

    # Create a simple EGIF for erasure demo
    simple_egif = '(Human "Socrates") (Mortal "Socrates")'

    result3 = interface.apply_transformation(
        TransformationRequest(
            source_egif=simple_egif,
            rule_name="ERA",
            target_area_description="sheet",
            operation_details={"selected_elements": ["e_0"]},  # Try to erase first edge
            description="Erase Human relation",
        )
    )

    print(f"Original: {simple_egif}")
    if result3.success:
        print(f"✅ Successfully erased element:")
        print(f"   Result: {result3.result_egif}")
    else:
        print(f"❌ Erasure failed: {result3.error_message}")
        print("   (This is expected - element IDs are auto-generated)")

    # Example 4: IT+ - Iteration (copying elements)
    print("\n📋 Example 4: Iteration (IT+) - Copy elements")
    print("-" * 50)

    result4 = interface.apply_transformation(
        TransformationRequest(
            source_egif='(Wise "Socrates")',
            rule_name="IT+",
            target_area_description="sheet",
            operation_details={
                "selected_elements": ["v_0"]
            },  # Try to iterate first vertex
            description="Iterate Socrates vertex",
        )
    )

    if result4.success:
        print(f"✅ Successfully iterated:")
        print(f'   From: (Wise "Socrates")')
        print(f"   To:   {result4.result_egif}")
    else:
        print(f"❌ Iteration failed: {result4.error_message}")

    return [result1, result2, result3, result4]


def interactive_transformation_demo():
    """Interactive demonstration allowing user to specify transformations."""

    interface = EGIFTransformationInterface()

    print("\n🎮 Interactive EGIF Transformation Demo")
    print("=" * 45)

    # Load available corpus files
    corpus_dir = Path("/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs")
    available_files = []

    if corpus_dir.exists():
        for graph_dir in corpus_dir.iterdir():
            if graph_dir.is_dir():
                json_file = graph_dir / f"{graph_dir.name}.json"
                if json_file.exists():
                    available_files.append(str(json_file))

    print(f"📁 Found {len(available_files)} corpus EGIFs")

    # Show example transformations
    examples = [
        {
            "name": "Insert relation in negative area",
            "egif": '~[ (Human "Plato") ~[ (Mortal "Plato") ] ]',
            "rule": "INS",
            "area": "second_negation",
            "content": '(Philosopher "Plato")',
            "description": "Add philosopher relation to inner negation",
        },
        {
            "name": "Add double cut around content",
            "egif": '(Loves "Alice" "Bob")',
            "rule": "DC+",
            "area": "sheet",
            "content": "",
            "description": "Wrap love relation in double cut",
        },
        {
            "name": "Complex nested insertion",
            "egif": '~[ (Student "John") ~[ ~[ (Smart "John") ] ] ]',
            "rule": "INS",
            "area": "inner_cut",
            "content": '(Hardworking "John")',
            "description": "Add hardworking to innermost area",
        },
    ]

    print("\n🎯 Example Transformations:")
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print(f"   Original: {example['egif']}")
        print(f"   Rule: {example['rule']}")
        print(f"   Target: {example['area']}")
        if example["content"]:
            print(f"   Insert: {example['content']}")
        print(f"   Goal: {example['description']}")

        # Apply the transformation
        try:
            if example["rule"] == "INS":
                result = interface.apply_transformation(
                    TransformationRequest(
                        source_egif=example["egif"],
                        rule_name=example["rule"],
                        target_area_description=example["area"],
                        operation_details={"insert_content": example["content"]},
                        description=example["description"],
                    )
                )
            else:
                result = interface.apply_transformation(
                    TransformationRequest(
                        source_egif=example["egif"],
                        rule_name=example["rule"],
                        target_area_description=example["area"],
                        operation_details={"selected_elements": []},
                        description=example["description"],
                    )
                )

            if result.success:
                print(f"   ✅ Result: {result.result_egif}")
            else:
                print(f"   ❌ Failed: {result.error_message}")

        except Exception as e:
            print(f"   ⚠️  Error: {e}")

    return examples


def transformation_summary():
    """Provide summary of transformation capabilities."""

    print("\n📋 EGIF Transformation Interface Summary")
    print("=" * 45)

    capabilities = {
        "Supported Rules": [
            "DC+ (Double Cut Insertion) - Add logical structure",
            "DC- (Double Cut Erasure) - Remove empty double cuts",
            "INS (Insertion) - Add content to negative areas",
            "ERA (Erasure) - Remove content from positive areas",
            "IT+ (Iteration) - Copy/duplicate elements",
            "IT- (Deiteration) - Remove duplicate elements",
        ],
        "Area Identification": [
            "'sheet' - Main sheet of assertion",
            "'first_cut' - First cut encountered",
            "'second_negation' - Inner negation area",
            "'inner_cut' - Innermost cut area",
            "Direct ElementID - Specific element ID",
        ],
        "Input Sources": [
            "Corpus JSON files with EGIF content",
            "Direct EGIF strings",
            "Generated EGIFs from previous transformations",
        ],
        "Output Formats": [
            "New EGIF strings",
            "EGI data structures",
            "Transformation reports with changes",
            "Success/failure status with error messages",
        ],
    }

    for category, items in capabilities.items():
        print(f"\n🎯 {category}:")
        for item in items:
            print(f"   • {item}")

    print(f"\n✨ Key Features:")
    print(f"   • Strict Peirce-Dau formalism compliance")
    print(f"   • Automatic area polarity calculation")
    print(f"   • Intelligent target area identification")
    print(f"   • Comprehensive error handling")
    print(f"   • Integration with existing EGIF parser/generator")
    print(f"   • Support for complex nested structures")


if __name__ == "__main__":
    print("🚀 Corpus EGIF Transformation System")
    print("=" * 40)

    # Run comprehensive demonstrations
    results = demonstrate_multiple_transformations()

    # Show interactive examples
    interactive_transformation_demo()

    # Provide capability summary
    transformation_summary()

    # Final status
    successful_transformations = sum(1 for r in results if r and r.success)
    print(f"\n🎉 Demo Complete!")
    print(f"   Successful transformations: {successful_transformations}/{len(results)}")
    print(f"   EGIF transformation interface is ready for use!")
