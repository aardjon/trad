///
/// Contains the central UI state.
///
library;

import 'package:flutter/material.dart';

/// The central GUI state.
///
/// This class contains all information that represent the current state of the GUI. Note that,
/// while the GUI doesn't explicitly show any state to the outside, it of course has some internal
/// state that must be kept centrally. But as this is still a UI internal implementation, it does
/// not store any kind of application/business state.
///
/// There should ever be only one instance of this class.
class GuiState {

  /// State flag storing whether the UI is currently initializing (true) or not (false).
  bool _isInitializing = true;

  /// The global navigation key instance.
  static final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  /// Defines whether the GUI is currently initializing
  ///
  /// While the UI is initializing, direct repaint is not possible. In this case, a repaint request
  /// must be delayed to the end of the current event frame. After initialization (i.e. after the
  /// app enters the central event loop), all repaints can be scheduled directly for better
  /// performance and to avoid race conditions between direct and delayed executions. Furthermore,
  /// all other state members may be empty/invalid during initialization.
  /// This flag is only set to false exactly once and then stays in this state forever.
  bool isInitializing() {
    return _isInitializing;
  }

  /// Changes the UI state to be initialized.
  void setInitialized() {
    _isInitializing = false;
  }

  /// Returns the global navigation key used for switching between pages.
  ///
  /// This key is needed for switching without having a `context` object.
  GlobalKey<NavigatorState> getNavigatorKey() {
    return _navigatorKey;
  }

}
