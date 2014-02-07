"""
Unit tests for checking default role of a user "Student" when he creates a course or
after deleting creates same course ageain
"""
from django.http import HttpRequest

from contentstore.tests.utils import AjaxEnabledTestClient
from contentstore.utils import delete_course_and_groups
from courseware.tests.factories import UserFactory
from xmodule.modulestore import Location
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from student.models import CourseEnrollment


class TestCourseListing(ModuleStoreTestCase):
    """
    Unit tests for checking enrollment and default role "Student" of a logged in user
    """
    def setUp(self):
        """
        Add a user and a course
        """
        super(TestCourseListing, self).setUp()
        # create and log in a staff user.
        self.user = UserFactory(is_staff=True)  # pylint: disable=no-member
        self.request = HttpRequest()
        self.request.user = self.user
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password='test')

        # create a course via the view handler to create course
        self.course_location = Location(['i4x', 'Org_1', 'Course_1', 'course', 'Run_1'])
        self._create_course_with_give_location(self.course_location)

    def _create_course_with_give_location(self, course_location):
        self.course_locator = loc_mapper().translate_location(
            course_location.course_id, course_location, False, True
        )
        resp = self.client.ajax_post(
            self.course_locator.url_reverse('course'),
            {
                'org': course_location.org,
                'number': course_location.course,
                'display_name': 'test course',
                'run': course_location.name,
            }
        )
        return resp

    def tearDown(self):
        """
        Reverse the setup
        """
        self.client.logout()
        ModuleStoreTestCase.tearDown(self)

    def test_user_role_on_course_create(self):
        """
        Test that a user enrolls and get "Student" role for the course which he creates and remains enrolled even
        the course is deleted but loses its "Student" role
        """
        course_id = self.course_location.course_id
        # check that user has enrollment for this course
        self.assertEqual(CourseEnrollment.enrollment_counts(course_id).get('total'), 1)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        # check that user has his default "Student" role for this course
        self.assertEqual(self.user.roles.count(), 1)
        self.assertEqual(self.user.roles.all()[0].name, 'Student')

        delete_course_and_groups(course_id, commit=True)
        # check that user's enrollment for this course is not deleted
        self.assertEqual(CourseEnrollment.enrollment_counts(course_id).get('total'), 1)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        # check that user has no role for this course after deleting it
        self.assertEqual(self.user.roles.count(), 0)

    def test_user_role_on_course_recreate(self):
        """
        Test that creating same course again after deleting it doesn't stop user to get
        their default "Student" role
        """
        course_id = self.course_location.course_id
        # check that user has enrollment for this course
        self.assertEqual(CourseEnrollment.enrollment_counts(course_id).get('total'), 1)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        # check that user has his default "Student" role for this course
        self.assertEqual(self.user.roles.count(), 1)
        self.assertEqual(self.user.roles.all()[0].name, 'Student')

        # delete this course and recreate this course with same user
        delete_course_and_groups(course_id, commit=True)
        resp = self._create_course_with_give_location(self.course_location)
        self.assertEqual(resp.status_code, 200)

        # check that user has his default "Student" role again for this course
        self.assertEqual(CourseEnrollment.enrollment_counts(course_id).get('total'), 1)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        # check that user has his default "Student" role for this course
        self.assertEqual(self.user.roles.count(), 1)
        self.assertEqual(self.user.roles.all()[0].name, 'Student')
