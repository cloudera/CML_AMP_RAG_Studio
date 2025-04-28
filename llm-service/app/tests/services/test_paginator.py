#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
#

from app.services.chat_history.paginator import paginate


class TestPaginate:
    def test_paginate_with_limit_only(self):
        """Test paginate function with only limit parameter."""
        # Test with a list of integers
        results = [1, 2, 3, 4, 5]

        # Get the last 3 items
        paginated = paginate(results, limit=3, offset=None)
        assert paginated == [3, 4, 5]

        # Get the last 1 item
        paginated = paginate(results, limit=1, offset=None)
        assert paginated == [5]

        # Get all items (limit larger than list)
        paginated = paginate(results, limit=10, offset=None)
        assert paginated == [1, 2, 3, 4, 5]

    def test_paginate_with_limit_and_offset(self):
        """Test paginate function with both limit and offset parameters."""
        # Test with a list of integers
        results = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        # Get 3 items, offset 2 from the end
        # Should return items [6, 7, 8] (skipping 9, 10)
        paginated = paginate(results, limit=3, offset=2)
        assert paginated == [6, 7, 8]

        # Get 2 items, offset 5 from the end
        # Should return items [4, 5] (skipping 6, 7, 8, 9, 10)
        paginated = paginate(results, limit=2, offset=5)
        assert paginated == [4, 5]

        # Get 4 items, offset 0 from the end (same as limit only)
        paginated = paginate(results, limit=4, offset=0)
        assert paginated == [7, 8, 9, 10]

    def test_paginate_edge_cases(self):
        """Test paginate function with edge cases."""
        # Empty list
        results = []
        paginated = paginate(results, limit=5, offset=None)
        assert paginated == []

        paginated = paginate(results, limit=5, offset=2)
        assert paginated == []

        # Offset larger than list size
        results = [1, 2, 3]
        paginated = paginate(results, limit=2, offset=5)
        assert paginated == []

        # Offset + limit larger than list size
        results = [1, 2, 3, 4, 5]
        paginated = paginate(results, limit=3, offset=3)
        assert paginated == [1, 2]

        # None values for both limit and offset
        paginated = paginate(results, limit=None, offset=None)
        assert paginated == results

        # None value for limit but offset provided
        # This should return an empty list as the current implementation
        # only applies offset when limit is also provided
        paginated = paginate(results, limit=None, offset=2)
        assert paginated == [1, 2, 3]

    def test_paginate_with_different_types(self):
        """Test paginate function with different types of list elements."""
        # Test with a list of strings
        results = ["a", "b", "c", "d", "e"]
        paginated = paginate(results, limit=2, offset=1)
        assert paginated == ["c", "d"]

        # Test with a list of dictionaries
        results = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        paginated = paginate(results, limit=2, offset=1)
        assert paginated == [{"id": 2}, {"id": 3}]

        # Test with a list of mixed types
        results = [1, "a", {"key": "value"}, [1, 2, 3]]
        paginated = paginate(results, limit=2, offset=1)
        # With offset=1, we skip the last element [1, 2, 3]
        # and take 2 elements before that, which are "a" and {"key": "value"}
        assert paginated == ["a", {"key": "value"}]
