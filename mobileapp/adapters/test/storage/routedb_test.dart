///
/// Unit tests for the adapters.storage.routedb library.
///
library;

import 'dart:io';

import 'package:file/memory.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

import 'package:adapters/boundaries/paths.dart';
import 'package:adapters/boundaries/repositories/database.dart';
import 'package:adapters/boundaries/repositories/filesystem.dart';
import 'package:adapters/storage/routedb.dart';
import 'package:crosscuttings/di.dart';

class PathProviderBoundaryMock extends Mock implements PathProviderBoundary {
  static const String appDataDir = '/application/data/dir';

  final FileSystemBoundary _fsBoundary;

  PathProviderBoundaryMock(FileSystemBoundary fsBoundary) : _fsBoundary = fsBoundary {
    _fsBoundary.getDirectory(appDataDir).createSync(recursive: true);
  }

  @override
  Future<Directory> getAppDataDir() async {
    return _fsBoundary.getDirectory(appDataDir);
  }
}

class FileSystemBoundaryMock extends Mock implements FileSystemBoundary {
  final MemoryFileSystem _memoryFs = MemoryFileSystem();

  @override
  String joinPaths(String basePath, String appendPath) {
    return '$basePath${Platform.pathSeparator}$appendPath';
  }

  @override
  File getFile(String filePath) {
    return _memoryFs.file(filePath);
  }

  @override
  Directory getDirectory(String directoryPath) {
    return _memoryFs.directory(directoryPath);
  }
}

class RelationalDatabaseBoundaryMock extends Mock implements RelationalDatabaseBoundary {}

/// Unit tests for the adapters.storage.routedb.RouteDbStorage class.
void main() {
  final RelationalDatabaseBoundaryMock rdbMock = RelationalDatabaseBoundaryMock();
  final FileSystemBoundary fileSystemMock = FileSystemBoundaryMock();
  final PathProviderBoundaryMock pathProviderMock = PathProviderBoundaryMock(fileSystemMock);
  final DependencyProvider di = DependencyProvider();

  di.registerFactory<PathProviderBoundary>(() => pathProviderMock);
  di.registerFactory<FileSystemBoundary>(() => fileSystemMock);
  di.registerSingleton<RelationalDatabaseBoundary>(() => rdbMock);

  tearDown(() {
    // Reset the mocks after each test case
    reset(rdbMock);
    reset(pathProviderMock);
    reset(fileSystemMock);
  });

  // The path to the route database file that should be used by the application.
  const String expectedDbFilePath = '${PathProviderBoundaryMock.appDataDir}/peaks.sqlite';

  /// Ensures that the storage is initialized correctly, meaning that connect() is called at the
  /// database
  ///  - with the expected database file path
  ///  - with the readOnly parameter set to true
  test('test initStorage', () async {
    RouteDbStorage storage = RouteDbStorage(di);
    await storage.initStorage();

    verify(() => rdbMock.connect(expectedDbFilePath, readOnly: true)).called(1);
  });

  /// Test cases for the importRouteDbFile() method
  group('test importRouteDbFile', () {
    final Directory userDownloadDir = fileSystemMock.getDirectory('/home/user/Downloads/');
    userDownloadDir.createSync(recursive: true);

    /// Ensures that trying to import a non-existing file throw a PathNotFoundException exception
    test('input file missing', () {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      RouteDbStorage storage = RouteDbStorage(di);

      expect(
        () async {
          await storage.importRouteDbFile('/file/not/found.sqlite');
        },
        throwsA(isA<PathNotFoundException>()),
      );
    });

    /// Ensures that importing works if there is no previous database to be replaced:
    /// - The destination file must be created
    /// - The destination file must be a copy of the source file
    /// - The source file must not be deleted
    /// - The source file must not be modified
    test('no previous database file', () async {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      String filePathToImport = '${userDownloadDir.path}trad-routedb-4711.sqlite';
      const String expectedFileContent = 'Imported file';

      // Create the database file to import
      fileSystemMock.getFile(filePathToImport).writeAsStringSync(expectedFileContent);

      expect(fileSystemMock.getDirectory(PathProviderBoundaryMock.appDataDir).existsSync(), isTrue);
      // Run the test case
      RouteDbStorage storage = RouteDbStorage(di);
      await storage.importRouteDbFile(filePathToImport);

      File sourceFile = fileSystemMock.getFile(filePathToImport);
      File destinationFile = fileSystemMock.getFile(expectedDbFilePath);

      // Both the destination and the source file must exist
      expect(sourceFile.existsSync(), isTrue);
      expect(destinationFile.existsSync(), isTrue);

      // Both files have the same (unmodified) content
      expect(sourceFile.readAsStringSync(), equals(expectedFileContent));
      expect(destinationFile.readAsStringSync(), equals(expectedFileContent));
    });

    /// Ensures that the existing database file is replaced during successful import:
    ///  - The previous destination file must have been replaced
    ///  - The destination file must be a copy of the source file
    ///  - The source file must not be deleted
    ///  - The source file must not be modified
    ///  - No other files must have been created in the destination directory
    test('replace existing database file', () async {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      String filePathToImport = '${userDownloadDir.path}trad-routedb-4711.sqlite';
      const String expectedFileContent = 'Imported file';

      // Create the database file to import
      fileSystemMock.getFile(filePathToImport).writeAsStringSync(expectedFileContent);

      // Create the existing destination file
      fileSystemMock.getFile(expectedDbFilePath).writeAsStringSync('Old file content');

      expect(fileSystemMock.getDirectory(PathProviderBoundaryMock.appDataDir).existsSync(), isTrue);
      // Run the test case
      RouteDbStorage storage = RouteDbStorage(di);
      await storage.importRouteDbFile(filePathToImport);

      File sourceFile = fileSystemMock.getFile(filePathToImport);
      File destinationFile = fileSystemMock.getFile(expectedDbFilePath);

      // Both the destination and the source file must exist
      expect(sourceFile.existsSync(), isTrue);
      expect(destinationFile.existsSync(), isTrue);

      // Both files have the same (unmodified) content
      expect(sourceFile.readAsStringSync(), equals(expectedFileContent));
      expect(destinationFile.readAsStringSync(), equals(expectedFileContent));

      // There are no other files (e.g. backups) left
      expect(userDownloadDir.listSync(recursive: true).length, equals(1));
    });
  });
}
