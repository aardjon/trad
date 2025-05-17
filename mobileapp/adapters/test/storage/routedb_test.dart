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
import 'package:adapters/src/storage/routedb/schema.dart';
import 'package:core/entities/errors.dart';
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
  setUpAll(() {
    // Register a default values that are used by mocktails `any` matcher
    registerFallbackValue(Query.table('example_table', <String>['example_column']));
  });

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

  /// Test cases for ensuring the correct behaviour for wrong storage started/stopped states
  group('StorageState constraints', () {
    /// Ensure that a StateError is thrown if the storage is already started
    test('importRouteDbFile', () async {
      // Simulate a STARTED repository
      when(rdbMock.isConnected).thenReturn(true);

      // Run the test case
      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.importRouteDbFile('/does/not/matter.sqlite');
      }, throwsStateError);
    });
  });

  /// Test cases for the startStorage() method
  group('test startStorage', () {
    /// Ensures that the storage is initialized correctly, meaning that connect() is called at the
    /// database
    ///  - with the expected database file path
    ///  - with the readOnly parameter set to true
    /// and executeQuery() is called once on the database
    test('successful start', () async {
      // Simulate a database with exactly compatible schema version
      when(() => rdbMock.executeQuery(any())).thenAnswer((_) async {
        return <ResultRow>[
          ResultRow(<String, Object?>{
            DatabaseMetadataTable.columnSchemaVersionMajor: supportedSchemaVersion.major,
            DatabaseMetadataTable.columnSchemaVersionMinor: supportedSchemaVersion.minor,
          }),
        ];
      });

      RouteDbStorage storage = RouteDbStorage(di);
      await storage.startStorage();

      verify(() => rdbMock.connect(expectedDbFilePath, readOnly: true)).called(1);
      verify(() => rdbMock.executeQuery(any())).called(1);
    });

    /// Ensures the correct behaviour in case the database file cannot be opened for some reason
    /// (e.g. file not found, permission error, not an SQLite file etc.): An
    /// InaccessibleStorageException shall be thrown.
    test('unable to open DB file', () async {
      when(
        () => rdbMock.connect(any(), readOnly: any(named: 'readOnly')),
      ).thenThrow(const PathAccessException('Fake permission failure', OSError()));

      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.startStorage();
      }, throwsA(isA<InaccessibleStorageException>()));
    });

    /// Ensures the correct behaviour in case the database file is a valid SQLite database but is of
    /// an unexpected format (i.e. not a trad route database): An InvalidStorageFormatException
    /// shall be thrown.
    test('invalid database format', () async {
      when(() => rdbMock.executeQuery(any())).thenThrow(Exception('Fake SQL query failure'));

      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.startStorage();
      }, throwsA(isA<InvalidStorageFormatException>()));
    });

    test('empty metadata table', () async {
      when(() => rdbMock.executeQuery(any())).thenAnswer((_) async {
        return <ResultRow>[];
      });

      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.startStorage();
      }, throwsA(isA<InvalidStorageFormatException>()));
    });

    /// Ensures that an IncompatibleStorageException is thrown if the database schema is of an
    /// incompatible version.
    /// Note: All the concrete "major VS. minor" versioning cases are tested on the Version class
    /// test within [version_test.dart], so we are good with having *any* incompatible version here.
    test('unsupported schema version', () async {
      when(() => rdbMock.executeQuery(any())).thenAnswer((_) async {
        return <ResultRow>[
          ResultRow(<String, Object?>{
            DatabaseMetadataTable.columnSchemaVersionMajor: supportedSchemaVersion.major + 1,
            DatabaseMetadataTable.columnSchemaVersionMinor: supportedSchemaVersion.minor,
          }),
        ];
      });

      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.startStorage();
      }, throwsA(isA<IncompatibleStorageException>()));
    });
  });

  /// Test cases for the importRouteDbFile() method
  group('test importRouteDbFile', () {
    final Directory userDownloadDir = fileSystemMock.getDirectory('/home/user/Downloads/');
    userDownloadDir.createSync(recursive: true);

    /// Ensures that trying to import a non-existing file throws a PathNotFoundException exception
    test('input file missing', () {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      RouteDbStorage storage = RouteDbStorage(di);

      expect(() async {
        await storage.importRouteDbFile('/file/not/found.sqlite');
      }, throwsA(isA<PathNotFoundException>()));
    });

    /// Ensures that importing works if there is no previous database to be replaced:
    /// - The destination file must be created
    /// - The destination file must be a copy of the source file
    /// - The source file must not be deleted
    /// - The source file must not be modified
    test('no previous database file', () async {
      // Simulate a stopped repository
      when(rdbMock.isConnected).thenReturn(false);

      // Simulate a database with exactly compatible schema version
      when(() => rdbMock.executeQuery(any())).thenAnswer((_) async {
        return <ResultRow>[
          ResultRow(<String, Object?>{
            DatabaseMetadataTable.columnSchemaVersionMajor: supportedSchemaVersion.major,
            DatabaseMetadataTable.columnSchemaVersionMinor: supportedSchemaVersion.minor,
          }),
        ];
      });

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
      // Simulate a database with exactly compatible schema version
      when(() => rdbMock.executeQuery(any())).thenAnswer((_) async {
        return <ResultRow>[
          ResultRow(<String, Object?>{
            DatabaseMetadataTable.columnSchemaVersionMajor: supportedSchemaVersion.major,
            DatabaseMetadataTable.columnSchemaVersionMinor: supportedSchemaVersion.minor,
          }),
        ];
      });

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

    /// Ensures the correct behaviour in case the file to import exists but cannot be read
    test('source file not readable', () async {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      when(
        () => rdbMock.connect(any(), readOnly: any(named: 'readOnly')),
      ).thenThrow(const PathAccessException('Fake permission failure', OSError()));
      // Create the database file to import
      String filePathToImport = '${userDownloadDir.path}trad-routedb-4711.sqlite';

      // Run the test case
      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.importRouteDbFile(filePathToImport);
      }, throwsA(isA<InaccessibleStorageException>()));
    });

    /// Ensures the correct behaviour in case the file to import is of an unknown format
    test('invalid source file format', () async {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      when(() => rdbMock.executeQuery(any())).thenThrow(Exception('Fake SQL query failure'));
      // Create the database file to import
      String filePathToImport = '${userDownloadDir.path}trad-routedb-4711.sqlite';

      // Run the test case
      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.importRouteDbFile(filePathToImport);
      }, throwsA(isA<InvalidStorageFormatException>()));
    });

    /// Ensures the correct behaviour in case the file to import has an incompatible schema
    test('incompatible schema version', () async {
      when(rdbMock.isConnected).thenReturn(false); // The storage is STOPPED
      when(() => rdbMock.executeQuery(any())).thenAnswer((_) async {
        return <ResultRow>[
          ResultRow(<String, Object?>{
            DatabaseMetadataTable.columnSchemaVersionMajor: supportedSchemaVersion.major + 1,
            DatabaseMetadataTable.columnSchemaVersionMinor: supportedSchemaVersion.minor,
          }),
        ];
      });
      // Create the database file to import
      String filePathToImport = '${userDownloadDir.path}trad-routedb-4711.sqlite';

      // Run the test case
      RouteDbStorage storage = RouteDbStorage(di);
      expect(() async {
        await storage.importRouteDbFile(filePathToImport);
      }, throwsA(isA<IncompatibleStorageException>()));
    });
  });
}
