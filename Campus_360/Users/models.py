from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Create your models here.


# 1. Describe here Model for Superadmin::
class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, role= "student", password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email!")
        
        if not username:
            raise ValueError("User must have an username!")

        email= self.normalize_email(email)
        user = self.model(
            email= email,
            username = username,
            first_name = first_name,
            last_name= last_name,
            role = role,
            **extra_fields
        )

        # reset all the boolean flags according to the role::
        user.is_admin = False
        user.is_teacher = False
        user.is_student = False

        #  set boolean flags role automatically::
        if role == "student":
            user.is_student = True
            user.is_approved = True  # Students auto approved 
        elif role == "teacher":
            user.is_teacher = True
            user.is_approved = False  # Teachers needs admin approval
        elif role == "admin":
            user.is_admin = True
            user.is_approved = True

        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user
    
    # Now create a function for superuser::
    def create_superuser(self, first_name, last_name, username, email, password=None, **extra_fields):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name= first_name,
            last_name= last_name,
            role = "admin",   # superuser role always be admins
            **extra_fields
        )

        # After creating this we need to give the permission::
        user.is_admin = True
        user.is_teacher = True
        user.is_student = True
        user.is_superadmin = True
        user.is_staff = True
        user.is_active = True
        user.is_approved = True
        user.save(using=self._db)
        return user



# 2. this is my MainUser  Model::
class MainUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES= [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("admin", "Admin"),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)
    username = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    roll_number = models.CharField(max_length=10, blank=True, null=True)
    regd_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=20, blank=True, null = True)

    # required
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)  # New field for approval status

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects= MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj = None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True