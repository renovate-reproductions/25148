# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from test.tools.mock_descriptors import make_message, make_field, make_enum
from src.comparator import wrappers
from google.protobuf import descriptor_pb2
from google.api import resource_pb2


class MessageTest(unittest.TestCase):
    def test_basic_properties(self):
        message = make_message("Foo")
        self.assertEqual(message.name, "Foo")
        self.assertEqual(message.proto_file_name, "foo")
        self.assertEqual(message.path, ())
        self.assertEqual(
            message.source_code_line,
            "No source code line can be identified by path ().",
        )

    def test_get_field(self):
        fields = (
            make_field(name="field_one", number=1),
            make_field(name="field_two", number=2),
        )
        message = make_message("Message", fields=fields)
        field_one = message.fields[1]
        self.assertTrue(isinstance(field_one, wrappers.Field))
        self.assertEqual(field_one.name, "field_one")

    def test_nested_types(self):
        # Create the inner message.
        inner_msg = [
            make_message(
                "InnerMessage",
                fields=(
                    make_field(
                        name="hidden_message",
                        number=1,
                    ),
                ),
            )
        ]
        inner_enums = [make_enum(name="InnerEnum")]
        inner_fields = [make_field("not_interesting")]

        # Create the outer message, which contains inner fields, enums, messages.
        outer_msg = make_message(
            "Outer",
            fields=inner_fields,
            nested_enums=inner_enums,
            nested_messages=inner_msg,
        )

        self.assertEqual(len(outer_msg.fields.keys()), 1)
        self.assertEqual(outer_msg.fields[1].name, "not_interesting")
        self.assertEqual(len(outer_msg.nested_enums.keys()), 1)
        self.assertEqual(
            outer_msg.nested_messages["InnerMessage"].fields[1].name, "hidden_message"
        )

    def test_resource_path(self):
        options = descriptor_pb2.MessageOptions()
        resource = options.Extensions[resource_pb2.resource]
        resource.pattern.append("foo/{foo}/bar")
        resource.pattern.append("foo/{foo}/bar/{bar}")
        resource.type = "example.v1/Bar"
        message = make_message("Test", options=options)

        self.assertEqual(message.resource.value.type, "example.v1/Bar")
        self.assertEqual(
            message.resource.value.pattern, ["foo/{foo}/bar", "foo/{foo}/bar/{bar}"]
        )

    def test_oneof_fields(self):
        oneof_field1 = make_field(name="field1", number=1, oneof=True)
        oneof_field2 = make_field(name="field2", number=2, oneof=True)
        non_oneof_field3 = make_field(name="field3", number=3, oneof=False)
        message = make_message(
            name="Message",
            fields=(
                oneof_field1,
                oneof_field2,
                non_oneof_field3,
            ),
        )
        self.assertEqual(len(message.oneof_fields), 2)
        self.assertEqual({x.name for x in message.oneof_fields}, {"field1", "field2"})

    def test_resource_annotation(self):
        options = descriptor_pb2.MessageOptions()
        resource = options.Extensions[resource_pb2.resource]
        resource.pattern.append("foo/{foo}/bar")
        resource.pattern.append("foo/{foo}/bar/{bar}")
        resource.type = "example/Bar"
        message = make_message("Message", options=options)
        message_without_resource = make_message("Message")
        self.assertEqual(message_without_resource.resource, None)
        self.assertEqual(message.resource.value.type, "example/Bar")
        self.assertEqual(
            message.resource.value.pattern, ["foo/{foo}/bar", "foo/{foo}/bar/{bar}"]
        )

    def test_source_code_line(self):
        L = descriptor_pb2.SourceCodeInfo.Location
        locations = [
            L(path=(4, 0, 2, 1), span=(1, 2, 3, 4)),
        ]
        message = make_message(
            proto_file_name="test.proto",
            locations=locations,
            path=(4, 0, 2, 1),
        )
        self.assertEqual(message.source_code_line, 2)
        self.assertEqual(message.proto_file_name, "test.proto")


if __name__ == "__main__":
    unittest.main()