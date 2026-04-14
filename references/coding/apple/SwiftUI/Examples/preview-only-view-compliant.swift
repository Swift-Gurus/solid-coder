import SwiftUI
//wrapped in preview block
// it will be exempt from review
// proper way of creating views for validation
#Preview {
    struct MyContentPreview: View {
        var body: some View {
            // assembly a view for testing
        }
        // other code to support it
    }

    struct MyContentPreviewModel {
    }



    // Return the preview view at the end of the closure
    return  MyContentPreview(
                     // passing dependencies
                   )
}