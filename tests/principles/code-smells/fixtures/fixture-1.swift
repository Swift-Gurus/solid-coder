/**
 solid-name: ReportComposer
 solid-category: service
 solid-description: Produces reports while exposing representative structural smells for workflow validation.
 */
struct ReportComposer {
    static func compose(for rows: [String]) -> String {
        if rows.isEmpty {
            return "Empty"
        }
        return rows.joined(separator: "\n")
    }

    func makeSection() {
        struct InlineSection {
            let title: String
        }

        _ = InlineSection(title: "Summary")
    }
}

/**
 solid-name: ReportEnvelope
 solid-category: model
 solid-description: Carries one rendered report without adding behavior.
 */
struct ReportEnvelope {
    let content: String
}
