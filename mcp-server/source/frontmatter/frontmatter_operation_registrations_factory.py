"""Composes source-backed metadata operations and bounded technology vocabulary."""

from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.operation_registration import OperationRegistration
from harness.project_context import ProjectDirectoryReading
from source.frontmatter.bind_frontmatter_descriptions_input import (
    BindFrontmatterDescriptionsInput,
)
from source.frontmatter.bind_frontmatter_descriptions_operation import (
    BindFrontmatterDescriptionsOperation,
)
from source.frontmatter.declaration_stack_resolver import DeclarationStackResolver
from source.frontmatter.frontmatter_category_resolver import FrontmatterCategoryResolver
from source.frontmatter.frontmatter_config_parser import FrontmatterConfigParser
from source.frontmatter.frontmatter_description_decisions import (
    FrontmatterDescriptionDecisions,
)
from source.frontmatter.frontmatter_preparation import FrontmatterPreparation
from source.frontmatter.prepare_frontmatter_input import PrepareFrontmatterInput
from source.frontmatter.prepare_frontmatter_operation import PrepareFrontmatterOperation
from source.frontmatter.stack_registration import StackRegistration
from source.source_frontmatter_reader_factory import SourceFrontmatterReaderFactory
from validation.collection_identity_binder import CollectionIdentityBinder
from validation.collection_identity_coverage_validator import (
    CollectionIdentityCoverageValidator,
)

_STACK_REGISTRATIONS = [
    StackRegistration(
        tag="swiftui",
        file_extensions=[".swift"],
        modules=["SwiftUI"],
        signals=[
            "View",
            "ViewModifier",
            "ViewBuilder",
            "PreviewProvider",
            "Text",
            "Image",
            "Button",
            "VStack",
            "HStack",
            "ZStack",
            "State",
            "Binding",
            "StateObject",
            "ObservedObject",
            "Environment",
            "EnvironmentObject",
            "List",
            "NavigationStack",
            "ScrollView",
            "GeometryReader",
            "Color",
            "Shape",
            "AnyView",
            "Form",
            "Section",
            "Preview",
        ],
    ),
    StackRegistration(
        tag="uikit",
        file_extensions=[".swift"],
        modules=["UIKit"],
        signals=[
            "UIView",
            "UIViewController",
            "UILabel",
            "UIButton",
            "UITableView",
            "UICollectionView",
            "UIApplication",
            "UIColor",
            "UIImage",
        ],
    ),
    StackRegistration(
        tag="appkit",
        file_extensions=[".swift"],
        modules=["AppKit"],
        signals=[
            "NSView",
            "NSViewController",
            "NSWindow",
            "NSApplication",
            "NSButton",
            "NSTextField",
            "NSColor",
            "NSImage",
        ],
    ),
    StackRegistration(
        tag="combine",
        file_extensions=[".swift"],
        modules=["Combine"],
        signals=[
            "Publisher",
            "AnyPublisher",
            "AnyCancellable",
            "Cancellable",
            "PassthroughSubject",
            "CurrentValueSubject",
            "Published",
            "ObservableObject",
        ],
    ),
    StackRegistration(
        tag="structured-concurrency",
        file_extensions=[".swift"],
        signals=[
            "async",
            "await",
            "actor",
            "Task",
            "TaskGroup",
            "ThrowingTaskGroup",
            "AsyncStream",
            "AsyncSequence",
            "Sendable",
            "MainActor",
            "nonisolated",
        ],
    ),
    StackRegistration(
        tag="gcd",
        file_extensions=[".swift"],
        modules=["Dispatch", "Foundation"],
        signals=[
            "DispatchQueue",
            "DispatchGroup",
            "DispatchSemaphore",
            "DispatchWorkItem",
            "DispatchSource",
            "DispatchTime",
        ],
    ),
    StackRegistration(
        tag="tca",
        file_extensions=[".swift"],
        modules=["ComposableArchitecture"],
        signals=[
            "Reducer",
            "ReducerOf",
            "Store",
            "StoreOf",
            "ViewStore",
            "WithViewStore",
            "ObservableState",
            "Effect",
            "EffectOf",
        ],
    ),
    StackRegistration(
        tag="core-data",
        file_extensions=[".swift"],
        modules=["CoreData"],
        signals=[
            "NSManagedObject",
            "NSManagedObjectContext",
            "NSPersistentContainer",
            "NSFetchRequest",
            "NSFetchedResultsController",
        ],
    ),
    StackRegistration(
        tag="swift-data",
        file_extensions=[".swift"],
        modules=["SwiftData"],
        signals=[
            "Model",
            "ModelContext",
            "ModelContainer",
            "PersistentModel",
            "Query",
            "FetchDescriptor",
        ],
    ),
    StackRegistration(
        tag="grdb",
        file_extensions=[".swift"],
        modules=["GRDB"],
        signals=[
            "DatabaseQueue",
            "DatabasePool",
            "Database",
            "FetchableRecord",
            "PersistableRecord",
            "TableRecord",
            "Row",
        ],
    ),
]


"""
solid-name: FrontmatterOperationRegistrationsFactory
solid-category: factory
solid-spec: [SPEC-069]
solid-description: Composes deterministic metadata preparation and evidenced description binding using shared source and configuration capabilities.
"""


class FrontmatterOperationRegistrationsFactory:
    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def make(self) -> list[OperationRegistration]:
        return [
            OperationRegistration(
                name="source.prepare_frontmatter",
                input_model=PrepareFrontmatterInput,
                output_model=FrontmatterPreparation,
                handler=PrepareFrontmatterOperation(
                    metadata=SourceFrontmatterReaderFactory().make(),
                    stacks=DeclarationStackResolver(_STACK_REGISTRATIONS),
                    configuration=FrontmatterConfigParser(),
                    project_directory=self._project_directory,
                    stack_registrations=_STACK_REGISTRATIONS,
                    categories=FrontmatterCategoryResolver(),
                ),
            ),
            OperationRegistration(
                name="source.bind_frontmatter_descriptions",
                input_model=BindFrontmatterDescriptionsInput,
                output_model=FrontmatterDescriptionDecisions,
                handler=BindFrontmatterDescriptionsOperation(
                    CollectionIdentityBinder(
                        CollectionIdentityCoverageValidator(
                            FlowValidationErrorFactory()
                        ),
                    ),
                ),
            ),
        ]
