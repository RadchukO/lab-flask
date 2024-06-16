delete from entries;

insert into entries(date, title, content, comment) values (now() - interval '10 days', 'First post!', 'This is my first post.  It is exciting!', '123');
insert into entries(date, title, content, comment) values (now() - interval '1 day', 'I love Flask', 'I am finding Flask incredibly fun.', '12345');
insert into entries(title, content, comment) values ('Databases', 'My databases class is a lot of work, but I am enjoying it.', '123456789');
