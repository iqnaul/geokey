import json
import os
import glob

from PIL import Image
from StringIO import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.core.exceptions import PermissionDenied
from django.conf import settings

from nose.tools import raises
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.renderers import JSONRenderer

from core.exceptions import MalformedRequestData
from projects.tests.model_factories import UserF, ProjectF
from dataviews.tests.model_factories import ViewFactory, RuleFactory
from contributions.models import ImageFile

from contributions.views.media import (
    MediaFileListAbstractAPIView, AllContributionsMediaAPIView,
    MediaFileSingleAbstractView, AllContributionsSingleMediaApiView,
    MyContributionsMediaApiView, MyContributionsSingleMediaApiView,
    GroupingContributionsMediaApiView, GroupingContributionsSingleMediaApiView
)

from ..model_factories import ObservationFactory
from .model_factories import ImageFileFactory, get_image


class MediaFileAbstractListAPIViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project}
        )

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/**/*'
        ))
        for f in files:
            os.remove(f)

    def render(self, response):
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {'blah': 'blubb'}
        return response.render()

    def test_get_list_and_respond(self):
        ImageFileFactory.create_batch(5, **{'contribution': self.contribution})

        url = reverse(
            'api:project_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.get(url)
        view = MediaFileListAbstractAPIView()
        view.request = request

        response = self.render(
            view.get_list_and_respond(self.admin, self.contribution)
        )
        self.assertEqual(len(json.loads(response.content)), 5)

    def test_create_and_respond(self):
        url = reverse(
            'api:project_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        data = {
            'name': 'A test image',
            'description': 'Test image description',
            'file': get_image()
        }

        request = self.factory.post(url, data)
        request.user = self.admin
        view = MediaFileListAbstractAPIView()
        view.request = request

        response = self.render(
            view.create_and_respond(self.admin, self.contribution)
        )

        response_json = json.loads(response.content)
        self.assertEqual(
            response_json.get('name'),
            data.get('name')
        )
        self.assertEqual(
            response_json.get('description'),
            data.get('description')
        )
        self.assertEqual(
            response_json.get('creator').get('display_name'),
            request.user.display_name
        )

    @raises(MalformedRequestData)
    def test_create_and_respond_without_file(self):
        url = reverse(
            'api:project_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        data = {
            'name': 'A test image',
            'description': 'Test image description'
        }

        request = self.factory.post(url, data)
        request.user = self.admin
        view = MediaFileListAbstractAPIView()
        view.request = request

        view.create_and_respond(self.admin, self.contribution)

    @raises(MalformedRequestData)
    def test_create_and_respond_without_name(self):
        url = reverse(
            'api:project_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        data = {
            'description': 'Test image description',
            'file': get_image()
        }

        request = self.factory.post(url, data)
        request.user = self.admin
        view = MediaFileListAbstractAPIView()
        view.request = request

        view.create_and_respond(self.admin, self.contribution)


    # def test_create_video_and_respond(self):
    #     url = reverse(
    #         'api:project_media',
    #         kwargs={
    #             'project_id': self.project.id,
    #             'contribution_id': self.contribution.id
    #         }
    #     )
    #
    #     video = open(
    #         '/home/oroick/opencomap/contributions/tests/media/video.MOV'
    #     )
    #
    #     data = {
    #         'name': 'A test image',
    #         'description': 'Test image description',
    #         'file': video
    #     }
    #
    #     request = self.factory.post(url, data)
    #     request.user = self.admin
    #     view = MediaFileListAbstractAPIView()
    #     view.request = request
    #
    #     response = self.render(
    #         view.create_and_respond(self.admin, self.contribution)
    #     )
    #
    #     response_json = json.loads(response.content)
    #     self.assertEqual(
    #         response_json.get('name'),
    #         data.get('name')
    #     )
    #     self.assertEqual(
    #         response_json.get('description'),
    #         data.get('description')
    #     )
    #     self.assertEqual(
    #         response_json.get('creator').get('display_name'),
    #         request.user.display_name
    #     )


class MediaFileSingleAbstractViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        self.image_file = ImageFileFactory.create(
            **{'contribution': self.contribution, 'creator': self.creator}
        )

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def render(self, response):
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {'blah': 'blubb'}
        return response.render()

    def test_get_and_respond(self):
        url = reverse(
            'api:project_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.get(url)
        view = MediaFileSingleAbstractView()
        view.request = request

        response = self.render(
            view.get_and_respond(
                self.admin,
                self.image_file
            )
        )
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('id'), self.image_file.id)

    @raises(ImageFile.DoesNotExist)
    def test_delete_and_respond_with_admin(self):
        url = reverse(
            'api:project_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.delete(url)
        view = MediaFileSingleAbstractView()
        view.request = request

        view.delete_and_respond(self.admin, self.image_file)
        ImageFile.objects.get(pk=self.image_file.id)

    @raises(ImageFile.DoesNotExist)
    def test_delete_and_respond_with_contributor(self):
        url = reverse(
            'api:project_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.delete(url)
        view = MediaFileSingleAbstractView()
        view.request = request

        view.delete_and_respond(self.creator, self.image_file)
        ImageFile.objects.get(pk=self.image_file.id)

    @raises(PermissionDenied)
    def test_delete_and_respond_with_some_dude(self):
        url = reverse(
            'api:project_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.delete(url)
        view = MediaFileSingleAbstractView()
        view.request = request

        view.delete_and_respond(UserF.create(), self.image_file)


class AllContributionsMediaAPIViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.viewer = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        ImageFileFactory.create_batch(5, **{'contribution': self.contribution})

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def get(self, user):
        url = reverse(
            'api:project_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.get(url)
        force_authenticate(request, user)
        view = AllContributionsMediaAPIView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id
        ).render()

    def post(self, user, data=None):
        if data is None:
            data = {
                'name': 'A test image',
                'description': 'Test image description',
                'file': get_image()
            }

        url = reverse(
            'api:project_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.post(
            url, data, content_type='multipart/form-data; boundary=---XXX---')
        force_authenticate(request, user)
        view = AllContributionsMediaAPIView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id
        ).render()

    def test_get_images_with_admin(self):
        response = self.get(self.admin)
        self.assertEqual(response.status_code, 200)

    def test_get_images_with_contributor(self):
        response = self.get(self.creator)
        self.assertEqual(response.status_code, 200)

    def test_get_images_with_some_dude(self):
        response = self.get(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_get_images_with_anonymous(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_admin(self):
        response = self.post(self.admin)
        print response
        self.assertEqual(response.status_code, 201)

    def test_upload_image_with_contributor(self):
        response = self.post(self.creator)
        self.assertEqual(response.status_code, 201)

    def test_upload_image_with_some_dude(self):
        response = self.post(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_anonymous(self):
        response = self.post(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_upload_unsupported_file_format(self):
        xyz_file = StringIO()
        xyz = Image.new('RGBA', size=(50, 50), color=(256, 0, 0))
        xyz.save(xyz_file, 'png')
        xyz_file.seek(0)

        data = {
            'name': 'A test image',
            'description': 'Test image description',
            'file': ContentFile(xyz_file.read(), 'test.xyz')
        }

        response = self.post(self.admin, data=data)
        self.assertEqual(response.status_code, 400)


class MyContributionsMediaApiViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.viewer = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        ImageFileFactory.create_batch(5, **{'contribution': self.contribution})

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def get(self, user):
        url = reverse(
            'api:mycontributions_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.get(url)
        force_authenticate(request, user)
        view = MyContributionsMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id
        ).render()

    def post(self, user, data=None):
        if data is None:
            data = {
                'name': 'A test image',
                'description': 'Test image description',
                'file': get_image()
            }

        url = reverse(
            'api:mycontributions_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.post(url, data)
        force_authenticate(request, user)
        view = MyContributionsMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id
        ).render()

    def test_get_images_with_admin(self):
        response = self.get(self.admin)
        self.assertEqual(response.status_code, 404)

    def test_get_images_with_contributor(self):
        response = self.get(self.creator)
        self.assertEqual(response.status_code, 200)

    def test_get_images_with_some_dude(self):
        response = self.get(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_get_images_with_anonymous(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_admin(self):
        response = self.post(self.admin)
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_contributor(self):
        response = self.post(self.creator)
        self.assertEqual(response.status_code, 201)

    def test_upload_image_with_some_dude(self):
        response = self.post(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_anonymous(self):
        response = self.post(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_upload_unsupported_file_format(self):
        xyz_file = StringIO()
        xyz = Image.new('RGBA', size=(50, 50), color=(256, 0, 0))
        xyz.save(xyz_file, 'png')
        xyz_file.seek(0)

        data = {
            'name': 'A test image',
            'description': 'Test image description',
            'file': ContentFile(xyz_file.read(), 'test.xyz')
        }

        response = self.post(self.creator, data=data)
        self.assertEqual(response.status_code, 400)


class GroupingContributionsMediaApiViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.viewer = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        self.viewer = UserF.create()
        self.grouping = ViewFactory.create(
            add_viewers=[self.viewer],
            **{'project': self.project}
        )
        RuleFactory.create(**{
            'view': self.grouping,
            'observation_type': self.contribution.observationtype
        })

        ImageFileFactory.create_batch(5, **{'contribution': self.contribution})

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def get(self, user):
        url = reverse(
            'api:grouping_media',
            kwargs={
                'project_id': self.project.id,
                'grouping_id': self.grouping.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.get(url)
        force_authenticate(request, user)
        view = GroupingContributionsMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            grouping_id=self.grouping.id,
            contribution_id=self.contribution.id
        ).render()

    def post(self, user, data=None):
        if data is None:
            data = {
                'name': 'A test image',
                'description': 'Test image description',
                'file': get_image()
            }

        url = reverse(
            'api:grouping_media',
            kwargs={
                'project_id': self.project.id,
                'grouping_id': self.grouping.id,
                'contribution_id': self.contribution.id
            }
        )

        request = self.factory.post(url, data)
        force_authenticate(request, user)
        view = GroupingContributionsMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            grouping_id=self.grouping.id,
            contribution_id=self.contribution.id
        ).render()

    def test_get_images_with_admin(self):
        response = self.get(self.admin)
        self.assertEqual(response.status_code, 200)

    def test_get_images_with_contributor(self):
        response = self.get(self.creator)
        self.assertEqual(response.status_code, 404)

    def test_get_images_with_viewer(self):
        response = self.get(self.viewer)
        self.assertEqual(response.status_code, 200)

    def test_get_images_with_some_dude(self):
        response = self.get(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_get_images_with_anonymous(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_admin(self):
        response = self.post(self.admin)
        self.assertEqual(response.status_code, 201)

    def test_upload_image_with_contributor(self):
        response = self.post(self.creator)
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_viewer(self):
        response = self.post(self.viewer)
        self.assertEqual(response.status_code, 403)

    def test_upload_image_with_some_dude(self):
        response = self.post(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_upload_image_with_anonymous(self):
        response = self.post(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_upload_unsupported_file_format(self):
        xyz_file = StringIO()
        xyz = Image.new('RGBA', size=(50, 50), color=(256, 0, 0))
        xyz.save(xyz_file, 'png')
        xyz_file.seek(0)

        data = {
            'name': 'A test image',
            'description': 'Test image description',
            'file': ContentFile(xyz_file.read(), 'test.xyz')
        }

        response = self.post(self.admin, data=data)
        self.assertEqual(response.status_code, 400)


class AllContributionsSingleMediaApiViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.viewer = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        self.image_file = ImageFileFactory.create(
            **{'contribution': self.contribution, 'creator': self.creator}
        )

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def get(self, user):
        url = reverse(
            'api:project_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.get(url)
        force_authenticate(request, user)
        view = AllContributionsSingleMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id,
            file_id=self.image_file.id
        ).render()

    def delete(self, user):
        url = reverse(
            'api:project_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.delete(url)
        force_authenticate(request, user)
        view = AllContributionsSingleMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id,
            file_id=self.image_file.id
        ).render()

    def test_get_image_with_admin(self):
        response = self.get(self.admin)
        self.assertEqual(response.status_code, 200)

    def test_get_image_with_contributor(self):
        response = self.get(self.creator)
        self.assertEqual(response.status_code, 200)

    def test_get_image_with_viewer(self):
        viewer = UserF.create()
        dataview = ViewFactory.create(
            add_viewers=[viewer],
            **{'project': self.project}
        )
        RuleFactory.create(**{
            'view': dataview,
            'observation_type': self.contribution.observationtype
        })
        response = self.get(viewer)
        self.assertEqual(response.status_code, 200)

    def test_get_image_with_some_dude(self):
        response = self.get(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_get_image_with_anonymous(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_admin(self):
        response = self.delete(self.admin)
        self.assertEqual(response.status_code, 204)

    def test_delete_image_with_contributor(self):
        response = self.delete(self.creator)
        self.assertEqual(response.status_code, 204)

    def test_delete_image_with_viewer(self):
        viewer = UserF.create()
        dataview = ViewFactory.create(
            add_viewers=[viewer],
            **{'project': self.project}
        )
        RuleFactory.create(**{
            'view': dataview,
            'observation_type': self.contribution.observationtype
        })
        response = self.delete(viewer)
        self.assertEqual(response.status_code, 403)

    def test_delete_image_with_some_dude(self):
        response = self.delete(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_anonymous(self):
        response = self.delete(AnonymousUser())
        self.assertEqual(response.status_code, 404)


class MyContributionsSingleMediaApiViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.viewer = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        self.image_file = ImageFileFactory.create(
            **{'contribution': self.contribution, 'creator': self.creator}
        )

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def get(self, user):
        url = reverse(
            'api:mycontributions_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.get(url)
        force_authenticate(request, user)
        view = MyContributionsSingleMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id,
            file_id=self.image_file.id
        ).render()

    def delete(self, user):
        url = reverse(
            'api:mycontributions_single_media',
            kwargs={
                'project_id': self.project.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.delete(url)
        force_authenticate(request, user)
        view = MyContributionsSingleMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            contribution_id=self.contribution.id,
            file_id=self.image_file.id
        ).render()

    def test_get_image_with_admin(self):
        response = self.get(self.admin)
        self.assertEqual(response.status_code, 404)

    def test_get_image_with_contributor(self):
        response = self.get(self.creator)
        self.assertEqual(response.status_code, 200)

    def test_get_image_with_viewer(self):
        viewer = UserF.create()
        dataview = ViewFactory.create(
            add_viewers=[viewer],
            **{'project': self.project}
        )
        RuleFactory.create(**{
            'view': dataview,
            'observation_type': self.contribution.observationtype
        })
        response = self.get(viewer)
        self.assertEqual(response.status_code, 404)

    def test_get_image_with_some_dude(self):
        response = self.get(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_get_image_with_anonymous(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_admin(self):
        response = self.delete(self.admin)
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_contributor(self):
        response = self.delete(self.creator)
        self.assertEqual(response.status_code, 204)

    def test_delete_image_with_viewer(self):
        viewer = UserF.create()
        dataview = ViewFactory.create(
            add_viewers=[viewer],
            **{'project': self.project}
        )
        RuleFactory.create(**{
            'view': dataview,
            'observation_type': self.contribution.observationtype
        })
        response = self.delete(viewer)
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_some_dude(self):
        response = self.delete(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_anonymous(self):
        response = self.delete(AnonymousUser())
        self.assertEqual(response.status_code, 404)


class GroupingContributionsSingleMediaApiViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = UserF.create()
        self.creator = UserF.create()
        self.viewer = UserF.create()
        self.project = ProjectF(
            add_admins=[self.admin],
            add_contributors=[self.creator]
        )

        self.contribution = ObservationFactory.create(
            **{'project': self.project, 'creator': self.creator}
        )

        self.viewer = UserF.create()
        self.grouping = ViewFactory.create(
            add_viewers=[self.viewer],
            **{'project': self.project}
        )
        RuleFactory.create(**{
            'view': self.grouping,
            'observation_type': self.contribution.observationtype
        })

        self.image_file = ImageFileFactory.create(
            **{'contribution': self.contribution, 'creator': self.creator}
        )

    def tearDown(self):
        files = glob.glob(os.path.join(
            settings.MEDIA_ROOT,
            'user-uploads/images/*'
        ))
        for f in files:
            os.remove(f)

    def get(self, user):
        url = reverse(
            'api:grouping_single_media',
            kwargs={
                'project_id': self.project.id,
                'grouping_id': self.grouping.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.get(url)
        force_authenticate(request, user)
        view = GroupingContributionsSingleMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            grouping_id=self.grouping.id,
            contribution_id=self.contribution.id,
            file_id=self.image_file.id
        ).render()

    def delete(self, user):
        url = reverse(
            'api:grouping_single_media',
            kwargs={
                'project_id': self.project.id,
                'grouping_id': self.grouping.id,
                'contribution_id': self.contribution.id,
                'file_id': self.image_file.id
            }
        )

        request = self.factory.delete(url)
        force_authenticate(request, user)
        view = GroupingContributionsSingleMediaApiView.as_view()
        return view(
            request,
            project_id=self.project.id,
            grouping_id=self.grouping.id,
            contribution_id=self.contribution.id,
            file_id=self.image_file.id
        ).render()

    def test_get_image_with_admin(self):
        response = self.get(self.admin)
        self.assertEqual(response.status_code, 200)

    def test_get_image_with_contributor(self):
        response = self.get(self.creator)
        self.assertEqual(response.status_code, 404)

    def test_get_image_with_viewer(self):
        response = self.get(self.viewer)
        self.assertEqual(response.status_code, 200)

    def test_get_image_with_some_dude(self):
        response = self.get(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_get_image_with_anonymous(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_admin(self):
        response = self.delete(self.admin)
        self.assertEqual(response.status_code, 204)

    def test_delete_image_with_contributor(self):
        response = self.delete(self.creator)
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_viewer(self):
        response = self.delete(self.viewer)
        self.assertEqual(response.status_code, 403)

    def test_delete_image_with_some_dude(self):
        response = self.delete(UserF.create())
        self.assertEqual(response.status_code, 404)

    def test_delete_image_with_anonymous(self):
        response = self.delete(AnonymousUser())
        self.assertEqual(response.status_code, 404)
