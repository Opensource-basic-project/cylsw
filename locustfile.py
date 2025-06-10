from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # 사용자 행동 간 간격 (1~3초)

    @task(2)
    def dashboard(self):
        self.client.get("/dashboard")

    @task(2)
    def plenary(self):
        self.client.get("/plenary")

    @task(2)
    def legislation_notice(self):
        self.client.get("/legislation_notice")

    @task(1)
    def foreign_legislation(self):
        self.client.get("/foreign_legislation")

    @task(1)
    def trends(self):
        self.client.get("/legislative_trends")

    @task(1)
    def example(self):
        self.client.get("/legislative_examples")

    @task(1)
    def example(self):
        self.client.get("/legislation_notice_ongoing")
    
    @task(1)
    def example(self):
        self.client.get("/legislation_notice_ended")
    
    @task(1)
    def example(self):
        self.client.get("/public_opinion")
        
       # /*보험, 마약,약물, 장애인복지*/