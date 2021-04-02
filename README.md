# dat_insta
Tìm các thông tin trên instagram mà người dùng không biết ví dụ như địa chỉ, các thông tin gmail sô đth tải tất cả các ảnh về máy tính với công cụ insta_find_dat

Để sử dụng chúng ta có thể dùng kali linux/mac/windows terminal nhưng khuyên nên dùng 

google terminal để tránh 1 số lỗi.... 

google terminal: https://console.cloud.google.com/ 

cài đặt:

1: tải file github: git clone https://github.com/s3777091/dat_insta

2: chạy vào file dat_insta

3: pip3 install -r requirements.txt

4: tạo file config: mkdir config

5: cd config

6: echo "tk người dùng insta của bạn" > tk.conf

7: echo "mk người dùng insta của bạn" > mk.conf

8: echo "{}" > settings.json

9: python3 insta_find_dat.py <tên người cần tìm>
ví dụ: python3 insta_find_dat.py alica_111

