from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from APP_NAME.ajax import ajax
from APP_NAME import views, settings

urlpatterns = patterns('',
    url(r'^$', views.Index().view, name='index'),
	url(r'^ajax/$', ajax, name='ajax'),
	url(r'^ajax/(?P<view>\w+)/$', ajax, name='ajax'),
	url(r'^do_reload/', views.do_reload, name='do_reload'),
	url(r'^resetPassword/$', views.resetPassword,name='resetPassword'),
    url(r'^admin/', include(admin.site.urls)),

	# login page
	url(r'^login_required/', views.Login().view, name='login_required'),
	url(r'^login_required/(?P<next_url>.+)', views.Login().view, name='login_required'),
	url(r'^email_not_validated/', views.InvalidEmail().view, name='invalid_email'),

	# email verification
	url(r'^resend_email_confirmation/', views.resend_email_confirmation, 
		name='resend_email_confirmation'),
	url(r'^email-verify/(?P<code>\w*)', views.verify_email, name='verify_email'),
	url(r'^mail-sent', views.mail_sent, name='mail_sent'),

	# Registration
	url(r'^userRegistration/$', views.userRegistration,name='userRegistration'),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    
