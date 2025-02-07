# _*_ encoding:utf-8 _*_
from django.shortcuts import render
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.db.models import Q


from .models import CourseOrg, CityDict, Teacher
from .forms import UserAskForm
from operation.models import UserFavorite, UserApply, UserEstimate, UserCourse, UserAppointment
from courses.models import Course
from utils.mixin_utils import LoginRequiredMixin
# Create your views here.


class OrgView(View):
    # 课程机构列表功能
    def get(self, request):
        # 课程机构
        all_orgs = CourseOrg.objects.all()
        hot_orgs = all_orgs.order_by("-click_num")[:3]
        # 城市
        all_citys = CityDict.objects.all()

        # 机构搜索
        search_keywords = request.GET.get('keyword', '')
        if search_keywords:
            all_orgs = all_orgs.filter(Q(name__icontains=search_keywords) | Q(deac__icontains=search_keywords))

        # 取出筛选城市,这里的是前端页面传递的city
        city_id = request.GET.get('city', "")
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))

        # 类别筛选
        category = request.GET.get('ct', "")
        if category:
            all_orgs = all_orgs.filter(category=category)

        sort = request.GET.get('sort', "")
        if sort:
            if sort == "students":
                all_orgs = all_orgs.order_by("-students")
            elif sort == "courses":
                all_orgs = all_orgs.order_by("-course_nums")
        org_nums = all_orgs.count()

        # 对课程机构进行分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_orgs, 5, request=request)  # 5表示每一页的数量
        orgs = p.page(page)

        return render(request, "org-list.html", {
            "all_orgs": orgs,
            "all_citys": all_citys,
            "org_nums": org_nums,
            "city_id": city_id,
            "category": category,
            "hot_orgs": hot_orgs,
            "sort": sort,
        })


# 用户添加咨询
class AddUserAskView(View):
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            user_ask = userask_form.save(commit=True)
            return HttpResponse("{'status':'success'}", content_type='application/json')  # json字符串
        else:
            return HttpResponse("{'status':'fail', 'msg':'添加出错'}",
                                content_type='application/json')


class OrgHomeView(View):
    """
    机构首页
    """
    def get(self, request, org_id):
        current_page = "home"
        course_org = CourseOrg.objects.get(id=int(org_id))
        course_org.click_num += 1
        course_org.save()
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_courses = course_org.course_set.all()[:3]
        all_teachers = course_org.teacher_set.all()[:1]
        return render(request, 'org-detail-homepage.html', {
            'all_courses': all_courses,
            'all_teachers': all_teachers,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgCourseView(View):
    """
    机构课程列表首页
    """
    def get(self, request, org_id):
        current_page = "course"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_courses = course_org.course_set.all()
        return render(request, 'org-detail-course.html', {
            'all_courses': all_courses,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgDescView(View):
    """
    机构介绍页
    """
    def get(self, request, org_id):
        current_page = "desc"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-desc.html', {
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgTeacherView(View):
    """
    机构教师页
    """
    def get(self, request, org_id):
        current_page = "teacher"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        all_teachers = course_org.teacher_set.all()
        return render(request, 'org-detail-teachers.html', {
            'all_teachers': all_teachers,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class AddFavView(View):
    """
    用户收藏，用户取消收藏
    """
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)
        fav_type = request.POST.get('fav_type', 0)

        if not request.user.is_authenticated():  # 判断用户是否登陆
            # 判断用户登陆状态
            return HttpResponse("{'status':'fail', 'msg':'用户未登录'}",
                                content_type='application/json')

        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=int(fav_id), fav_type=int(fav_type))
        if exist_records:
            # 如果记录已经存在，表示用户取消收藏
            exist_records.delete()
            if int(fav_type) == 1:
                course = Course.objects.get(id=int(fav_id))
                course.fav_nums -= 1
                if course.fav_nums < 0:
                    course.fav_nums = 0
                course.save()
            elif int(fav_type) == 2:
                course_org = CourseOrg.objects.get(id=int(fav_id))
                course_org.fav_num -= 1
                if course_org.fav_nums < 0:
                    course_org.fav_nums = 0
                course_org.save()
            elif int(fav_type) == 3:
                teacher = Teacher.objects.get(id=int(fav_id))
                teacher.fav_num -= 1
                if teacher.fav_nums < 0:
                    teacher.fav_nums = 0
                teacher.save()
            return HttpResponse("{'status':'success', 'msg':'收藏'}",
                                content_type='application/json')
        else:
            user_fav = UserFavorite()
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(fav_id)
                user_fav.fav_type = int(fav_type)
                user_fav.save()

                if int(fav_type) == 1:
                    course = Course.objects.get(id=int(fav_id))
                    course.fav_nums += 1
                    course.save()
                elif int(fav_type) == 2:
                    course_org = CourseOrg.objects.get(id=int(fav_id))
                    course_org.fav_num += 1
                    course_org.save()
                elif int(fav_type) == 3:
                    teacher = Teacher.objects.get(id=int(fav_id))
                    teacher.fav_num += 1
                    teacher.save()
                return HttpResponse("{'status':'success', 'msg':'已收藏'}",
                                    content_type='application/json')
            else:
                return HttpResponse("{'status':'fail', 'msg':'收藏失败'}",
                                    content_type='application/json')


class AddApplyView(View):
    """
    用户课程报名
    """
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)

        if not request.user.is_authenticated():  # 判断用户是否登陆
            # 判断用户登陆状态
            return HttpResponse("{'status':'fail', 'msg':'用户未登录'}",
                                content_type='application/json')

        exist_records = UserApply.objects.filter(user=request.user, fav_id=int(fav_id))
        user_course = UserCourse.objects.filter(user=request.user)
        if exist_records:
            # 如果记录已经存在，表示用户取消报名
            exist_records.delete()
            user_course.delete()
            course = Course.objects.get(id=int(fav_id))
            course.students -= 1
            if course.students < 0:
                course.students = 0
            course.save()
            return HttpResponse("{'status':'success', 'msg':'报名'}",
                                content_type='application/json')
        else:
            user_apply = UserApply()
            user_course = UserCourse()
            course = Course.objects.get(id=int(fav_id))
            if int(fav_id) > 0 and course.students < course.limit and request.user.category == 1:
                user_apply.user = request.user
                user_apply.fav_id = int(fav_id)
                user_apply.save()

                user_course.user = request.user
                user_course.course = course
                user_course.save()

                course.students += 1
                course.save()
                return HttpResponse("{'status':'success', 'msg':'已报名'}",
                                    content_type='application/json')
            elif course.students >= course.limit:
                return HttpResponse("{'status':'fail', 'msg':'名额已满'}",
                                    content_type='application/json')
            elif request.user.category != 1:
                return HttpResponse("{'status':'fail', 'msg':'您还不是会员呢'}",
                                    content_type='application/json')
            else:
                return HttpResponse("{'status':'fail', 'msg':'报名失败'}",
                                    content_type='application/json')


class AddAppointmentView(View):
    """
    用户课程预约
    """
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)

        if not request.user.is_authenticated():  # 判断用户是否登陆
            # 判断用户登陆状态
            return HttpResponse("{'status':'fail', 'msg':'用户未登录'}",
                                content_type='application/json')

        exist_records = UserAppointment.objects.filter(user=request.user, fav_id=int(fav_id))
        # user_course = UserCourse.objects.filter(user=request.user)
        if exist_records:
            # 如果记录已经存在，表示用户取消报名
            exist_records.delete()
            return HttpResponse("{'status':'success', 'msg':'预约'}",
                                content_type='application/json')
        else:
            user_appointment = UserAppointment()
            if int(fav_id) > 0 and request.user.category == 0:
                user_appointment.user = request.user
                user_appointment.fav_id = int(fav_id)
                user_appointment.save()

                return HttpResponse("{'status':'success', 'msg':'已预约'}",
                                    content_type='application/json')
            elif request.user.category != 0:
                return HttpResponse("{'status':'fail', 'msg':'您已经是会员啦'}",
                                    content_type='application/json')
            else:
                return HttpResponse("{'status':'fail', 'msg':'预约失败'}",
                                    content_type='application/json')


class AddEstimateView(View):
    """
    教师满意度评估
    """
    def post(self, request):
        estimate = request.POST.get('estimate', 0)

        if not request.user.is_authenticated():  # 判断用户是否登陆
            # 判断用户登陆状态
            return HttpResponse("{'status':'fail', 'msg':'用户未登录'}",
                                content_type='application/json')
        # 查询已存在的记录
        exist_records = UserEstimate.objects.filter(user=request.user, estimate=int(estimate))
        if exist_records:
            # 如果记录已经存在，表示用户取消
            exist_records.delete()
            return HttpResponse("{'status':'success', 'msg':'报名'}",
                                content_type='application/json')
        else:
            user_estimate = UserEstimate()
            if int(estimate) > 0 and request.user.category == 1:
                user_estimate.user = request.user
                user_estimate.estimate = int(estimate)
                user_estimate.save()
                return HttpResponse("{'status':'success', 'msg':'已报名'}",
                                    content_type='application/json')
            elif request.user.category != 1:
                return HttpResponse("{'status':'fail', 'msg':'您还不是会员呢'}",
                                    content_type='application/json')
            else:
                return HttpResponse("{'status':'fail', 'msg':'报名失败'}",
                                    content_type='application/json')


class TeacherListView(View):
    """
    课程讲师列表页
    """
    def get(self, request):
        all_teachers = Teacher.objects.all()
        teacher_count = all_teachers.count()

        # 机构搜索
        search_keywords = request.GET.get('keyword', '')
        if search_keywords:
            all_teachers = all_teachers.filter(Q(name__icontains=search_keywords)
                                               | Q(work_position__icontains=search_keywords)
                                               | Q(work_years__icontains=search_keywords)
                                               | Q(work_company__icontains=search_keywords))
        sort = request.GET.get('sort', "")
        if sort == 'teacher':
            all_teachers = all_teachers.filter(category=0)
        elif sort == 'expert':
            all_teachers = all_teachers.filter(category=1)
        # if sort:
        #     if sort == "hot":
        #         all_teachers = all_teachers.order_by("-click_num")

        sorted_teacher = Teacher.objects.all().order_by("-click_num")[:3]
        # 对讲师进行分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_teachers, 5, request=request)  # 5表示每一页的数量
        teachers = p.page(page)

        return render(request, "teachers-list.html", {
            "all_teachers": teachers,
            "sorted_teacher": sorted_teacher,
            "sort": sort,
            'teacher_count': teacher_count,
        })


class TeacherDetailView(View):
    def get(self, request, teacher_id):
        teacher = Teacher.objects.get(id=int(teacher_id))
        teacher.click_num += 1
        teacher.save()
        all_courses = Course.objects.filter(teacher=teacher)

        has_teacher_faved = False
        if UserFavorite.objects.filter(user=request.user, fav_type=3, fav_id=teacher.id):
            has_teacher_faved = True

        has_org_faved = False
        if UserFavorite.objects.filter(user=request.user, fav_type=2,  fav_id=teacher.org.id):
            has_org_faved = True
        # 讲师排行
        sorted_teacher = Teacher.objects.all().order_by("-click_num")[:3]

        return render(request, "teacher-detail.html", {
            'teacher': teacher,
            'all_courses': all_courses,
            "sorted_teacher": sorted_teacher,
            'has_teacher_faved': has_teacher_faved,
            'has_org_faved': has_org_faved
        })
