import 'dart:convert';

class PluginRequest {
  const PluginRequest({required this.id, required this.method, this.params = const {}});
  final int id;
  final String method;
  final Map<String, dynamic> params;

  factory PluginRequest.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final method = json['method'];
    final params = json['params'];
    if (id is! int || method is! String || (params != null && params is! Map)) {
      throw const FormatException('invalid plugin request');
    }
    return PluginRequest(id: id, method: method, params: Map<String, dynamic>.from(params as Map? ?? const {}));
  }

  factory PluginRequest.fromLine(String line) =>
      PluginRequest.fromJson(jsonDecode(line) as Map<String, dynamic>);
}

String successResponse(int id, Object? result) => jsonEncode({'jsonrpc': '2.0', 'id': id, 'result': result});
String errorResponse(int id, String message) => jsonEncode({'jsonrpc': '2.0', 'id': id, 'error': {'message': message}});
