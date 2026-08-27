import type { Chunk, DocumentDetail, DocumentSummary } from "@/lib/types"

/**
 * Mock document library.
 *
 * All entities (companies, plaintiffs, apps) are fictional placeholders —
 * these exist only to give the UI realistic-looking structural chunking
 * and citations to render before the real ingest pipeline exists.
 */
export const mockDocuments: DocumentDetail[] = [
  {
    id: "doc-msla",
    title: "Master Software License Agreement — Northwind Systems / Acme Robotics",
    type: "contract",
    status: "ready",
    source: "SEC EDGAR (sample)",
    chunkCount: 10,
    ingestedAt: "2026-08-10",
    sections: [
      {
        id: "art-1",
        heading: "Article 1 — Definitions",
        clauses: [
          {
            id: "1.1",
            heading: "“Software”",
            text: "“Software” means the object-code version of Northwind's proprietary routing-optimization platform, including any Updates provided under this Agreement, but excluding any Third-Party Components identified in Exhibit B.",
          },
          {
            id: "1.2",
            heading: "“Update”",
            text: "“Update” means any patch, bug fix, or minor version release that Northwind makes generally available to licensees at no additional charge during the Term.",
          },
        ],
      },
      {
        id: "art-2",
        heading: "Article 2 — Grant of License",
        clauses: [
          {
            id: "2.1",
            heading: "License Grant",
            text: "Subject to the terms of this Agreement, Northwind grants Licensee a non-exclusive, non-transferable, worldwide license to install and use the Software solely for Licensee's internal business operations.",
          },
          {
            id: "2.2",
            heading: "Restrictions",
            text: "Licensee shall not sublicense, reverse engineer, or distribute the Software to any third party except as expressly permitted under Section 4.3 (Authorized Resellers).",
          },
        ],
      },
      {
        id: "art-4",
        heading: "Article 4 — Fees and Payment",
        clauses: [
          {
            id: "4.1",
            heading: "License Fees",
            text: "Licensee shall pay the annual license fee set forth in Exhibit A within thirty (30) days of the invoice date.",
          },
          {
            id: "4.2(a)",
            heading: "Late Payment",
            text: "Any amount not paid when due shall accrue interest at the lesser of 1.5% per month or the maximum rate permitted by law.",
          },
          {
            id: "4.2(b)",
            heading: "Suspension for Non-Payment",
            text: "If any invoiced amount remains unpaid for more than sixty (60) days, Northwind may suspend Licensee's access to the Software until payment is received in full, as defined in Section 3.2.",
          },
        ],
      },
      {
        id: "art-7",
        heading: "Article 7 — Termination",
        clauses: [
          {
            id: "7.1",
            heading: "Termination for Cause",
            text: "Either party may terminate this Agreement upon thirty (30) days' written notice if the other party materially breaches this Agreement and fails to cure within that period.",
          },
          {
            id: "7.2",
            heading: "Effect of Termination",
            text: "Upon termination, Licensee shall cease all use of the Software and certify in writing the destruction of all copies within ten (10) business days.",
          },
        ],
      },
      {
        id: "art-9",
        heading: "Article 9 — Limitation of Liability",
        clauses: [
          {
            id: "9.1",
            heading: "Cap on Damages",
            text: "Neither party's aggregate liability arising out of this Agreement shall exceed the total fees paid by Licensee in the twelve (12) months preceding the claim.",
          },
        ],
      },
    ],
  },
  {
    id: "doc-cdpa",
    title: "Example Consumer Data Protection Act",
    type: "statute",
    status: "ready",
    source: "State legislature (sample)",
    chunkCount: 8,
    ingestedAt: "2026-08-05",
    sections: [
      {
        id: "sec-1",
        heading: "§ 1. Definitions",
        clauses: [
          {
            id: "§1(a)",
            heading: "“Personal data”",
            text: "“Personal data” means any information that is linked or reasonably linkable to an identified or identifiable individual, excluding de-identified data or publicly available information.",
          },
          {
            id: "§1(b)",
            heading: "“Controller”",
            text: "“Controller” means the entity that, alone or jointly with others, determines the purpose and means of processing personal data.",
          },
        ],
      },
      {
        id: "sec-2",
        heading: "§ 2. Consumer Rights",
        clauses: [
          {
            id: "§2(a)",
            heading: "Right to Access",
            text: "A consumer has the right to confirm whether a controller is processing the consumer's personal data and to access that data.",
          },
          {
            id: "§2(b)",
            heading: "Right to Deletion",
            text: "A consumer has the right to request that a controller delete personal data that the consumer has provided to, or that the controller has obtained about, the consumer.",
          },
        ],
      },
      {
        id: "sec-3",
        heading: "§ 3. Controller Obligations",
        clauses: [
          {
            id: "§3(a)",
            heading: "Response Timeline",
            text: "A controller shall respond to a consumer request under Section 2 without undue delay, and in no case later than forty-five (45) days after receipt.",
          },
          {
            id: "§3(b)",
            heading: "Data Minimization",
            text: "A controller shall limit the collection of personal data to what is adequate, relevant, and reasonably necessary for the disclosed purposes of processing.",
          },
        ],
      },
      {
        id: "sec-6",
        heading: "§ 6. Enforcement",
        clauses: [
          {
            id: "§6(a)",
            heading: "Cure Period",
            text: "Prior to initiating an enforcement action, the enforcing authority shall provide the controller sixty (60) days' written notice and an opportunity to cure the alleged violation.",
          },
          {
            id: "§6(b)",
            heading: "Civil Penalty",
            text: "A controller that fails to cure a violation within the period specified in Section 6(a) is subject to a civil penalty not to exceed $7,500 per violation.",
          },
        ],
      },
    ],
  },
  {
    id: "doc-doe-v-example",
    title: "Doe v. Example Robotics Corp.",
    type: "case_law",
    status: "ready",
    source: "CourtListener (sample)",
    chunkCount: 6,
    ingestedAt: "2026-07-28",
    sections: [
      {
        id: "opinion",
        heading: "Opinion",
        clauses: [
          {
            id: "¶1",
            heading: "Background",
            text: "Plaintiff Jane Doe alleges that Defendant Example Robotics Corp. terminated her employment in retaliation for reporting a safety violation, in breach of the whistleblower protections of the Example Labor Code.",
          },
          {
            id: "¶4",
            heading: "Standard of Review",
            text: "On a motion for summary judgment, the court views the evidence in the light most favorable to the non-moving party and draws all reasonable inferences in that party's favor.",
          },
          {
            id: "¶7",
            heading: "Causation",
            text: "To establish a prima facie case of retaliation, Plaintiff must show that she engaged in a protected activity, suffered an adverse employment action, and that a causal link exists between the two.",
          },
          {
            id: "¶9",
            heading: "Temporal Proximity",
            text: "The court finds that termination occurring eleven days after Plaintiff's safety report is sufficiently close in time to support an inference of causation at the summary judgment stage.",
          },
          {
            id: "¶12",
            heading: "Holding",
            text: "For the foregoing reasons, Defendant's motion for summary judgment is DENIED as to Plaintiff's retaliation claim and GRANTED as to Plaintiff's defamation claim.",
          },
        ],
      },
    ],
  },
  {
    id: "doc-nimbus-tos",
    title: "Terms of Service — Nimbus Notes",
    type: "tos",
    status: "ready",
    source: "Public web (sample)",
    chunkCount: 6,
    ingestedAt: "2026-08-18",
    sections: [
      {
        id: "tos-account",
        heading: "Your Account",
        clauses: [
          {
            id: "3.1",
            heading: "Eligibility",
            text: "You must be at least 16 years old to create a Nimbus Notes account. By creating an account, you represent that you meet this requirement.",
          },
          {
            id: "3.2",
            heading: "Account Security",
            text: "You are responsible for maintaining the confidentiality of your login credentials and for all activity that occurs under your account.",
          },
        ],
      },
      {
        id: "tos-content",
        heading: "Your Content",
        clauses: [
          {
            id: "5.1",
            heading: "License to Nimbus",
            text: "You retain ownership of content you upload. You grant Nimbus a limited license to host, back up, and display that content solely to provide the Service to you.",
          },
        ],
      },
      {
        id: "tos-termination",
        heading: "Termination",
        clauses: [
          {
            id: "8.1",
            heading: "Termination by You",
            text: "You may stop using the Service and delete your account at any time from the account settings page.",
          },
          {
            id: "8.2",
            heading: "Termination by Nimbus",
            text: "We may suspend or terminate your account if you violate these Terms, including by attempting to circumvent usage limits described in Section 4.4.",
          },
          {
            id: "8.3",
            heading: "Data Retention After Termination",
            text: "Following termination, we retain your content for thirty (30) days to allow for account recovery, after which it is permanently deleted.",
          },
        ],
      },
    ],
  },
]

export const mockDocumentSummaries: DocumentSummary[] = mockDocuments.map((doc) => ({
  id: doc.id,
  title: doc.title,
  type: doc.type,
  status: doc.status,
  source: doc.source,
  chunkCount: doc.chunkCount,
  ingestedAt: doc.ingestedAt,
}))

export function getDocumentById(id: string): DocumentDetail | undefined {
  return mockDocuments.find((doc) => doc.id === id)
}

/** Flattens a document's Section > Clause tree into retrievable chunks. */
export function getChunksForDocument(documentId: string): Chunk[] {
  const doc = getDocumentById(documentId)
  if (!doc) return []
  return doc.sections.flatMap((section) =>
    section.clauses.map((clause) => ({
      id: `${documentId}:${clause.id}`,
      documentId,
      sectionId: section.id,
      clauseId: clause.id,
      heading: clause.heading,
      text: clause.text,
    })),
  )
}
