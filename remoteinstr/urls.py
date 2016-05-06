"""remoteinstr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from remoteinstrapp.views import generic_views
from remoteinstrapp.views import direct_command_views


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/instruments/$', generic_views.InstrumentList.as_view(), name='instrument-list'),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/$',
        generic_views.InstrumentDetailViewSet.as_view({'get': 'obtain', 'put': 'modify', 'delete':'remove'})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/$',
        direct_command_views.CommandViewSet.as_view({'get': 'obtain_command_list', })),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/query/$',
        direct_command_views.CommandQueryViewSet.as_view({'post': 'perform_query'})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/write_raw/$',
        direct_command_views.CommandWriteRawViewSet.as_view({'post': 'perform_write_raw',})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/query_raw/$',
        direct_command_views.CommandQueryRawViewSet.as_view({'post': 'perform_query_raw',})),

    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/read/$',
        direct_command_views.CommandReadViewSet.as_view({'post': 'perform_query',})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/write/$',
        direct_command_views.CommandWriteViewSet.as_view({'post': 'perform_query',})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/read_raw/$',
        direct_command_views.CommandReadRawViewSet.as_view({'post': 'perform_query',})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/commands/get_visa_attribute/$',
        direct_command_views.CommandGetVisaAttrViewSet.as_view({'post': 'perform_query',})),

    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/capabilities/$',
        generic_views.CapabilitiesList.as_view(), name='capabilities-list'),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/capabilities/(?P<capability>[^/]+)/$',
        generic_views.CapabilitiesDetail.as_view({'put': 'put_capabilities','get': 'get_capabilities','delete':'delete_capability'})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/characteristics/$',
        generic_views.CharacteristicsList.as_view(), name='characteristics-list'),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/characteristics/(?P<characteristic>[^/]+)/$',
        generic_views.CharacteristicsDetail.as_view({'put': 'put_characteristics','get': 'get_characteristics','delete':'delete_characteristics'})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/tasks/$',
        generic_views.TasksViewList.as_view(), name='tasksview-list'),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/tasks/(?P<taskId>[^/]+)/$',
        generic_views.TaskViewDetail.as_view({'put': 'put_task','get': 'get_task','delete':'delete_task'})),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/tasks/(?P<taskId>[^/]+)/commands/$',
        generic_views.CommandViewList.as_view(), name='command-view-list'),
    url(r'^v1/instruments/(?P<instrumentId>[^/]+)/tasks/(?P<taskId>[^/]+)/commands/(?P<commandId>[^/]+)/$',
        generic_views.CommandViewDetail.as_view({'put': 'put_command','get': 'get_command','delete':'delete_command'})),
    url(r'^v1/config/$', generic_views.ConfigViewDetail.as_view({'get':'list_config','put':'update_config'}), name='config-view'),
    url(r'^v1/config/instruments/$', generic_views.ConfigInstrumentViewDetail.as_view({'get':'list_config', 'put':'update_config_instrument'}),
        name='config-instruments-view'),
    url(r'^v1/config/instruments/backends/$',generic_views.ConfigInstrumentBackendsViewDetail.as_view({'get':'list'}),
        name='config-instruments-backends-view'),
    url(r'^v1/config/instruments/discover/$', generic_views.ConfigInstrumentDiscoverViewDetail.as_view({'get':'list'}),
        name='config-instruments-discover-view'),
    url(r'^v1/config/tasks/$', generic_views.ConfigTaskViewDetail.as_view({'get':'list_config', 'put':'update_config_task'}),
        name='config-tasks-view'),


]
