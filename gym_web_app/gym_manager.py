import pickle as cPickle
import os

class GymManager:
    def __init__(self):
        if os.path.exists("gym_manager.bin"):
            self.load()
        else:
            self.customers = dict()
            self.packages = dict()
            self.subscriptions = dict()
            self.payments = dict()

    def addCustomer(self, customer):
        customerId = customer.getCustomerId()
        self.customers[customerId] = customer
        self.subscriptions[customerId] = dict()
        self.payments[customerId] = dict()
        self.save()

    def addPackage(self, package):
        self.packages[package.getPackageId()] = package
        self.save()

    def addSubscription(self, customer, package, months):
        packageId = package.getPackageId()
        customerId = customer.getCustomerId()
        self.subscriptions[customerId][packageId] = months
        self.save()

    def addPayment(self, customer, package, amount):
        packageId = package.getPackageId()
        customerId = customer.getCustomerId()

        if packageId not in self.subscriptions[customerId]:
            print("No subscription found for this package.")
            return

        if packageId not in self.payments[customerId]:
            self.payments[customerId][packageId] = 0

        self.payments[customerId][packageId] += amount
        self.subscriptions[customerId][packageId] -= 1
        self.save()

    def save(self):
        with open("gym_manager.bin", "wb") as f:
            cPickle.dump(self, f)

    def load(self):
        with open("gym_manager.bin", "rb") as f:
            data = cPickle.load(f)
            self.customers = data.customers
            self.packages = data.packages
            self.subscriptions = data.subscriptions
            self.payments = data.payments

    # ✅ ADD THESE METHODS INSIDE CLASS (correct indentation)

    def deleteCustomer(self, customerId):
        if customerId in self.customers:
            del self.customers[customerId]
            del self.subscriptions[customerId]
            del self.payments[customerId]
            self.save()

    def getCustomerById(self, customerId):
        return self.customers.get(customerId)

    def updateCustomer(self, customerId, name, phone, date):
        if customerId in self.customers:
            customer = self.customers[customerId]
            customer.name = name
            customer.phone = phone
            customer.joiningDate = date
            self.save()