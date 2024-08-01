///
/// Unit tests for the core.usecases.knowledgebase library.
///
library;

import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

import 'package:core/boundaries/presentation.dart';
import 'package:core/boundaries/storage/knowledgebase.dart';
import 'package:core/entities/knowledgebase.dart';
import 'package:core/usecases/knowledgebase.dart';
import 'package:crosscuttings/di.dart';

class KnowledgebaseStorageBoundaryMock extends Mock implements KnowledgebaseStorageBoundary {}

class PresentationBoundaryMock extends Mock implements PresentationBoundary {}

/// Unit tests for the core.usecases.knowledgebase component.
void main() {
  group('core.usecases.knowledgebase', () {
    final DependencyProvider di = DependencyProvider();
    final KnowledgebaseStorageBoundaryMock storageBoundaryMock = KnowledgebaseStorageBoundaryMock();
    final PresentationBoundaryMock presentationBoundaryMock = PresentationBoundaryMock();

    // Configure DI to provide the boundary mocks
    di.registerFactory<KnowledgebaseStorageBoundary>(() => storageBoundaryMock);
    di.registerFactory<PresentationBoundary>(() => presentationBoundaryMock);

    setUpAll(() {
      // Register a default document object which is used by mocktails `any` matcher
      registerFallbackValue(
        KnowledgebaseDocument('FallbackID', 'Fallback Title', 'Fallback Content'),
      );
    });

    tearDown(() {
      // Reset the mocks after each test case
      reset(storageBoundaryMock);
      reset(presentationBoundaryMock);
    });

    /// Ensures the correct behaviour of the showDocumentPage() method:
    ///  - The requested document ID must be loaded from the storage (loadDocument())
    ///  - The document returned by the storage must be sent to the UI (showKnowledgebaseDocument())
    test('showDocumentPage() use case', () async {
      KnowledgebaseDocumentId testedDocumentId = 'dummyId';
      KnowledgebaseDocument testedDocument =
          KnowledgebaseDocument(testedDocumentId, 'title', 'content');
      // Setup the storage mock
      when(() => storageBoundaryMock.loadDocument(any())).thenAnswer((_) async {
        return testedDocument;
      });

      // Run the actual test case
      KnowledgebaseUseCases usecases = KnowledgebaseUseCases(di);
      await usecases.showDocumentPage(testedDocumentId);

      // Make sure the requested document is loaded from the storage
      verify(() => storageBoundaryMock.loadDocument(testedDocumentId)).called(1);
      // Make sure the retrieved document is sent to the UI
      verify(() => presentationBoundaryMock.showKnowledgebaseDocument(testedDocument)).called(1);
    });

    /// Ensures the correct behaviour of the showHomePage() method:
    ///  - The ID of the home document must be retrieved from the storage (getHomeIdentifier())
    ///  - The home document itself must be loaded from the storage (loadDocument())
    ///  - The document returned by the storage must be sent to the UI (showKnowledgebaseDocument())
    test('showHomePage() use case', () async {
      KnowledgebaseDocumentId homeDocumentId = 'indexId';
      KnowledgebaseDocument homeDocument =
          KnowledgebaseDocument(homeDocumentId, 'Home', 'Page index');
      // Setup the storage mock
      when(storageBoundaryMock.getHomeIdentifier).thenReturn(homeDocumentId);
      when(() => storageBoundaryMock.loadDocument(any())).thenAnswer((_) async {
        return homeDocument;
      });

      // Run the actual test case
      KnowledgebaseUseCases usecases = KnowledgebaseUseCases(di);
      await usecases.showHomePage();

      // Make sure the home document ID is retrieved
      verify(storageBoundaryMock.getHomeIdentifier).called(1);
      // Make sure the requested document is loaded from the storage
      verify(() => storageBoundaryMock.loadDocument(homeDocumentId)).called(1);
      // Make sure the retrieved document is sent to the UI
      verify(() => presentationBoundaryMock.showKnowledgebaseDocument(homeDocument)).called(1);
    });
  });
}
