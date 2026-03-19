import SwiftUI

// ❌ Depends on the analysis
// if there is no callers to this view
// we assume its for preview only, thus its Severe violation
struct MyContentPreview: View {
    var body: some View {
        // assembly a view for testing
    }
    // other code to support it
}

// ❌ These helper types also ship in production — dead code
// code to support MyContentPreview
struct MyContentPreviewModel {
}


// The #Preview references the file-scope struct but doesn't contain it
#Preview {
    MyContentPreview(
      // passing dependencies
    )
}