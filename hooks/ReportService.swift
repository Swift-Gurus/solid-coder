/**
solid-description: Coordinates the end-to-end lifecycle of fetching, rendering, and delivering reports to recipients.
solid-category: service
*/

class ReportService {
    private let db: Database
    private let mailer: Mailer
    private let pdfRenderer: PDFRenderer

    init(db: Database, mailer: Mailer, pdfRenderer: PDFRenderer) {
        self.db = db
        self.mailer = mailer
        self.pdfRenderer = pdfRenderer
    }

    func fetchData(for reportId: String) -> [Row] {
        return db.query("SELECT * FROM reports WHERE id = \(reportId)")
    }

    func renderPDF(rows: [Row]) -> Data {
        return pdfRenderer.render(rows)
    }

    func emailReport(to: String, pdf: Data) {
        mailer.send(to: to, attachment: pdf)
    }
}