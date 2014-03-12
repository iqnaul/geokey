import datetime
import factory

from projects.tests.model_factories import UserF

from ..models import Application


class ApplicationFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Application

    name = factory.Sequence(lambda n: 'name_%d' % n)
    description = factory.LazyAttribute(lambda o: '%s description' % o.name)
    created_at = datetime.date(2014, 11, 11)
    creator = factory.SubFactory(UserF)
    download_url = 'http://example.com'
    redirect_url = 'http://example.com/app'
    status = 'active'
